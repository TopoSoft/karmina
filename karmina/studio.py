"""Tenant-scoped production workflow. No model calls or agent engine here."""
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


AGENTS = [
    {'id': 'producer', 'output': 'production_brief', 'depends_on': [], 'instruction': 'Define audience, intent, constraints, deliverables and unresolved production decisions.'},
    {'id': 'writer', 'output': 'script', 'depends_on': ['producer'], 'instruction': 'Write a three-beat short story from the approved production brief. Preserve author intent.'},
    {'id': 'art_director', 'output': 'visual_bible', 'depends_on': ['writer'], 'instruction': 'Define character, world and style continuity for the selected production mode.'},
    {'id': 'director', 'output': 'shot_list', 'depends_on': ['art_director'], 'instruction': 'Translate the approved script and visual bible into three editable timed shots.'},
    {'id': 'sound_designer', 'output': 'sound_plan', 'depends_on': ['director'], 'instruction': 'Plan dialogue, ambience and music without assuming voice or music rights.'},
    {'id': 'reviewer', 'output': 'production_review', 'depends_on': ['sound_designer'], 'instruction': 'Review completeness, continuity risks, rights and missing evidence. Never certify unrendered media.'},
]


class StudioError(Exception):
    def __init__(self, code, status=400):
        super().__init__(code)
        self.code, self.status = code, status


def text(value, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise StudioError('invalid_input')
    return value.strip()


def now():
    return datetime.now(timezone.utc).isoformat()


class Studio:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS projects (tenant_id TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, PRIMARY KEY (tenant_id, id))')

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def _get(self, db, tenant, project_id):
        row = db.execute('SELECT data FROM projects WHERE tenant_id=? AND id=?', (tenant, project_id)).fetchone()
        if not row:
            raise StudioError('not_found', 404)
        return json.loads(row[0])

    def get(self, tenant, project_id):
        with closing(self.connect()) as db:
            return self._get(db, tenant, project_id)

    def list(self, tenant):
        with closing(self.connect()) as db:
            return [json.loads(row[0]) for row in db.execute('SELECT data FROM projects WHERE tenant_id=? ORDER BY rowid DESC', (tenant,))]

    def create(self, tenant, data):
        if not isinstance(data, dict) or set(data) - {'title', 'brief', 'mode', 'language'}:
            raise StudioError('invalid_input')
        if data.get('mode') not in ('animation', 'photorealistic') or data.get('language') not in ('en', 'lv', 'ru'):
            raise StudioError('invalid_input')
        p = {'id': str(uuid4()), 'title': text(data.get('title'), 120), 'brief': text(data.get('brief'), 12000), 'mode': data['mode'], 'language': data['language'], 'version': 0, 'status': 'development', 'created_at': now(), 'runtime': 'local_template', 'steps': [{'agent_id': a['id'], 'status': 'pending', 'artifact': None, 'history': []} for a in AGENTS], 'events': []}
        with closing(self.connect()) as db, db:
            db.execute('INSERT INTO projects VALUES (?, ?, ?)', (tenant, p['id'], json.dumps(p)))
        return p

    def _change(self, tenant, project_id, role, version, action, content=None, runtime='local_template'):
        if runtime != 'local_template':
            raise StudioError('runtime_unavailable', 503)
        if type(version) is not int or version < 0:
            raise StudioError('invalid_input')
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            p = self._get(db, tenant, project_id)
            if p['version'] != version:
                raise StudioError('version_conflict', 409)
            index = next((i for i, a in enumerate(AGENTS) if a['id'] == role), None)
            if index is None:
                raise StudioError('not_found', 404)
            step = p['steps'][index]
            if any(s['status'] != 'approved' for s in p['steps'][:index]):
                raise StudioError('dependency_not_approved', 409)
            if step['status'] == 'approved':
                raise StudioError('approved_immutable', 409)
            if action == 'draft':
                artifact_content = text(content, 24000) if content is not None else template(p, role)
                artifact = {'id': str(uuid4()), 'kind': AGENTS[index]['output'], 'revision': len(step['history']) + 1, 'content': artifact_content, 'source': 'human' if content is not None else 'local_template', 'created_at': now(), 'input_artifact_ids': [s['artifact']['id'] for s in p['steps'][:index]]}
                step['artifact'] = artifact
                step['history'].append(artifact)
                step['status'] = 'review'
            elif action == 'approve' and step['status'] == 'review':
                step['status'] = 'approved'
            else:
                raise StudioError('artifact_required', 409)
            p['version'] += 1
            p['events'].append({'seq': p['version'], 'type': action, 'agent_id': role, 'artifact_id': step['artifact']['id'], 'occurred_at': now()})
            if all(s['status'] == 'approved' for s in p['steps']):
                p['status'] = 'preproduction_ready'
            db.execute('UPDATE projects SET data=? WHERE tenant_id=? AND id=?', (json.dumps(p), tenant, project_id))
        return p

    def draft(self, tenant, project_id, role, version, content=None, runtime='local_template'):
        return self._change(tenant, project_id, role, version, 'draft', content, runtime)

    def approve(self, tenant, project_id, role, version):
        return self._change(tenant, project_id, role, version, 'approve')

    def export(self, tenant, project_id):
        p = self.get(tenant, project_id)
        if p['status'] != 'preproduction_ready':
            raise StudioError('incomplete_project', 409)
        return {'schema_version': 1, 'project_id': p['id'], 'project_version': p['version'], 'title': p['title'], 'mode': p['mode'], 'language': p['language'], 'media_generated': False, 'artifacts': [s['artifact'] for s in p['steps']]}


def template(project, role):
    """Explicit starter worksheets, not generated creative output or model reviews."""
    labels = {
        'en': ['Production brief', 'Script worksheet', 'Visual bible', 'Shot list', 'Sound plan', 'Production review', 'Original brief', 'Complete this worksheet before approving. No AI or media generation has run.'],
        'lv': ['Produkcijas uzdevums', 'Scenārija veidlapa', 'Vizuālā rokasgrāmata', 'Kadru saraksts', 'Skaņas plāns', 'Produkcijas pārbaude', 'Sākotnējais uzdevums', 'Aizpildiet veidlapu pirms apstiprināšanas. AI un mediju ģenerēšana nav veikta.'],
        'ru': ['Продюсерский бриф', 'Рабочий сценарий', 'Визуальная библия', 'План кадров', 'Звуковой план', 'Проверка производства', 'Исходный замысел', 'Заполните шаблон перед утверждением. AI и генерация медиа не запускались.'],
    }
    prompts = {
        'en': {
            'producer': 'Audience:\nPurpose:\nDuration: 24 seconds\nDeliverables:\nRights and budget: not approved',
            'writer': 'Opening (0–8s):\nChange (8–16s):\nResolution (16–24s):\nDialogue:',
            'art_director': 'Character references:\nLocations:\nPalette and lighting:\nContinuity constraints:\nAnimation: preserve original line work.\nCinema: confirm fictional casting and likeness permissions.',
            'director': 'Shot 1 | 0–8s | Establishing | Action:\nShot 2 | 8–16s | Medium | Action:\nShot 3 | 16–24s | Close-up | Action:\nCamera and continuity notes:',
            'sound_designer': 'Dialogue and voice permissions:\nAmbience:\nMusic license:\nTiming and mix notes:',
            'reviewer': 'Check approved upstream artifacts manually.\nContinuity evidence: no rendered frames.\nRights evidence: verify before production.\nBudget: no paid execution approved.\nMedia: not generated.\nUnresolved issues:',
        },
        'ru': {
            'producer': 'Аудитория:\nЗадача:\nДлительность: 24 секунды\nРезультат:\nПрава и бюджет: не утверждены',
            'writer': 'Завязка (0–8с):\nПерелом (8–16с):\nРазвязка (16–24с):\nДиалоги:',
            'art_director': 'Референсы персонажей:\nЛокации:\nПалитра и свет:\nПравила постоянства:\nАнимация: сохранить авторский штрих.\nКино: проверить права на внешность и образы.',
            'director': 'Кадр 1 | 0–8с | Общий план | Действие:\nКадр 2 | 8–16с | Средний план | Действие:\nКадр 3 | 16–24с | Крупный план | Действие:\nКамера и постоянство:',
            'sound_designer': 'Диалоги и права на голоса:\nАтмосфера:\nЛицензия музыки:\nТайминг и сведение:',
            'reviewer': 'Вручную проверить утверждённые материалы.\nПостоянство: готовых кадров пока нет.\nПрава: проверить до производства.\nБюджет: платный запуск не разрешён.\nМедиа: не созданы.\nОткрытые вопросы:',
        },
        'lv': {
            'producer': 'Auditorija:\nMērķis:\nIlgums: 24 sekundes\nRezultāts:\nTiesības un budžets: nav apstiprināti',
            'writer': 'Sākums (0–8s):\nPavērsiens (8–16s):\nAtrisinājums (16–24s):\nDialogi:',
            'art_director': 'Tēlu atsauces:\nVietas:\nPalete un gaisma:\nNepārtrauktības noteikumi:\nAnimācija: saglabāt autora līnijas.\nKino: pārbaudīt tēlu un līdzības atļaujas.',
            'director': 'Kadrs 1 | 0–8s | Kopplāns | Darbība:\nKadrs 2 | 8–16s | Vidējais plāns | Darbība:\nKadrs 3 | 16–24s | Tuvplāns | Darbība:\nKamera un nepārtrauktība:',
            'sound_designer': 'Dialogi un balss atļaujas:\nVide:\nMūzikas licence:\nLaiks un miksēšana:',
            'reviewer': 'Manuāli pārbaudīt apstiprinātos materiālus.\nNepārtrauktība: nav renderētu kadru.\nTiesības: pārbaudīt pirms ražošanas.\nBudžets: maksas izpilde nav atļauta.\nMediji: nav ģenerēti.\nAtvērtie jautājumi:',
        },
    }
    language = project['language']
    index = next(i for i, a in enumerate(AGENTS) if a['id'] == role)
    l = labels[language]
    return f"# {l[index]}\n\n{project['title']}\n\n{l[6]}: {project['brief']}\n\n{prompts[language][role]}\n\n{l[7]}"
