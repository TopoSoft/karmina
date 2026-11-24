import { messages } from './i18n.js';
const $ = id => document.getElementById(id);
let language = localStorage.getItem('karmina-language') || 'ru';
if (!messages[language]) language = 'ru';
let project = null, selected = 0, projects = [], busy = false;
const t = key => messages[language][key] || messages[language].internal_error;
const dirty = () => project && $('content').value !== (project.steps[selected].artifact?.content || '');
const leave = () => !dirty() || window.confirm(t('unsaved'));
function error(code) { $('error').textContent = t(code); $('error').hidden = false; }
async function api(path, data) {
  let response;
  try { response = await fetch(path, data === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); }
  catch { throw new Error('network_error'); }
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'internal_error');
  return result;
}
async function execute(action) {
  if (busy) return;
  busy = true;
  $('error').hidden = true;
  document.body.classList.add('busy');
  try { await action(); } catch (e) { error(e.message); }
  finally { busy = false; document.body.classList.remove('busy'); }
}
function localize() {
  document.documentElement.lang = language;
  $('language').value = language;
  document.querySelectorAll('[data-t]').forEach(el => { el.textContent = t(el.dataset.t); });
  renderProjects();
  if (project) render();
}
function renderProjects() {
  $('projects').replaceChildren();
  if (!projects.length) { const p = document.createElement('p'); p.textContent = t('empty'); $('projects').append(p); }
  projects.forEach(p => {
    const button = document.createElement('button');
    button.className = 'project-link' + (p.id === project?.id ? ' active' : '');
    button.textContent = p.title;
    button.onclick = () => { if (leave()) execute(async () => open(await api(`/api/projects/${p.id}`))); };
    $('projects').append(button);
  });
}
function open(p) {
  project = p;
  selected = Math.max(0, p.steps.findIndex(s => s.status !== 'approved'));
  $('create').hidden = true; $('studio').hidden = false;
  render(); renderProjects();
}
function render() {
  const step = project.steps[selected];
  const unlocked = project.steps.slice(0, selected).every(s => s.status === 'approved');
  const approved = step.status === 'approved';
  $('project-mode').textContent = t(project.mode);
  $('project-title').textContent = project.title;
  $('project-brief').textContent = project.brief;
  $('progress').textContent = `${project.steps.filter(s => s.status === 'approved').length} / 6 ${t('completed')}`;
  $('export').disabled = project.status !== 'preproduction_ready';
  $('pipeline').replaceChildren();
  project.steps.forEach((s, i) => {
    const button = document.createElement('button');
    button.className = 'stage ' + s.status + (i === selected ? ' selected' : '');
    button.setAttribute('aria-pressed', String(i === selected));
    const number = document.createElement('span'); number.className = 'stage-number'; number.textContent = String(i + 1).padStart(2, '0');
    const title = document.createElement('strong'); title.textContent = t(s.agent_id);
    const status = document.createElement('small'); status.textContent = t(s.status === 'pending' && project.steps.slice(0, i).every(prev => prev.status === 'approved') ? 'ready' : s.status);
    button.append(number, title, status);
    button.onclick = () => { if (!busy && leave()) { selected = i; render(); } };
    $('pipeline').append(button);
  });
  $('role-title').textContent = t(step.agent_id);
  $('revision').textContent = step.artifact ? `${t('revision')} ${step.artifact.revision} / ${t('source_' + step.artifact.source)}` : '';
  $('stage-hint').textContent = t(!unlocked ? 'locked' : approved ? 'immutable' : 'editable');
  $('content').value = step.artifact?.content || '';
  $('content').disabled = !unlocked || approved;
  $('draft').disabled = !unlocked || approved || Boolean(step.artifact);
  $('save').disabled = !unlocked || approved;
  $('approve').disabled = !unlocked || approved || !step.artifact;
  $('history').replaceChildren();
  [...step.history].reverse().forEach(a => {
    const detail = document.createElement('details');
    const summary = document.createElement('summary'); summary.textContent = `${t('revision')} ${a.revision} / ${t('source_' + a.source)}`;
    const pre = document.createElement('pre'); pre.textContent = a.content;
    detail.append(summary, pre); $('history').append(detail);
  });
}
async function change(action, content) {
  const role = project.steps[selected].agent_id;
  project = await api(`/api/projects/${project.id}/steps/${role}/${action}`, { version: project.version, ...(content === undefined ? {} : { content }) });
  if (action === 'approve' && selected < 5) selected++;
  render();
}
$('project-form').onsubmit = event => {
  event.preventDefault();
  execute(async () => {
    const fields = Object.fromEntries(new FormData(event.target));
    open(await api('/api/projects', { ...fields, language }));
    projects = (await api('/api/projects')).projects;
    event.target.reset(); renderProjects();
  });
};
$('new').onclick = () => { if (!busy && leave()) { project = null; $('create').hidden = false; $('studio').hidden = true; renderProjects(); } };
$('language').onchange = () => {
  if (!leave()) { $('language').value = language; return; }
  language = $('language').value; localStorage.setItem('karmina-language', language); localize();
};
$('draft').onclick = () => execute(() => change('draft'));
$('save').onclick = () => execute(() => change('draft', $('content').value));
$('approve').onclick = () => execute(async () => { if (dirty()) await change('draft', $('content').value); await change('approve'); });
$('export').onclick = () => execute(async () => {
  const pack = await api(`/api/projects/${project.id}/export`);
  const url = URL.createObjectURL(new Blob([JSON.stringify(pack, null, 2)], { type: 'application/json' }));
  const a = document.createElement('a'); a.href = url; a.download = `karmina-${project.id}.json`; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
window.addEventListener('beforeunload', event => { if (dirty()) { event.preventDefault(); event.returnValue = ''; } });
localize();
execute(async () => { projects = (await api('/api/projects')).projects; renderProjects(); });
