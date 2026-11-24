import { messages } from './i18n.js';

const $ = id => document.getElementById(id);
const roles = ['producer', 'writer', 'art_director', 'director', 'sound_designer', 'reviewer'];
const art = mode => mode === 'photorealistic' ? '/assets/cinema.png' : '/assets/crew.png';
let language = localStorage.getItem('karmina-language') || 'ru';
if (!messages[language]) language = 'ru';
let project = null, selected = 0, projects = [], busy = false, activeAgent = null;
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

function setView(studio, push = true) {
  $('landing').hidden = studio;
  $('workspace').hidden = !studio;
  document.body.classList.toggle('in-studio', studio);
  if (push) history.pushState(null, '', studio ? '/studio' : '/');
  document.title = studio && project ? `${project.title} / Karmina` : 'Karmina / Film studio';
  if (push) window.scrollTo({ top: 0, behavior: 'instant' });
}
function enterStudio(mode) {
  if (busy || !leave()) return;
  if ($('agent-dialog').open) $('agent-dialog').close();
  if (dirty()) render();
  if (mode) newProject(mode);
  setView(true);
}
function newProject(mode) {
  project = null;
  $('project-form').reset();
  if (mode) $('project-form').elements.mode.value = mode;
  $('create-art').src = art($('project-form').elements.mode.value);
  $('create').hidden = false;
  $('studio').hidden = true;
  renderProjects();
}
function goHome(section) {
  if (busy || !leave()) return;
  if (dirty()) render();
  setView(false);
  if (section) {
    history.replaceState(null, '', '/#' + section);
    $(section).scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
  }
}
function localize() {
  document.documentElement.lang = language;
  $('language').value = language;
  document.querySelectorAll('[data-t]').forEach(el => { el.textContent = t(el.dataset.t); });
  document.querySelectorAll('[data-t-aria]').forEach(el => { el.setAttribute('aria-label', t(el.dataset.tAria)); });
  renderProjects();
  renderCrew();
  if (project) render();
  if (activeAgent) fillAgent(activeAgent);
}
function renderCrew() {
  $('crew-grid').replaceChildren();
  roles.forEach(role => {
    const button = document.createElement('button');
    button.className = 'crew-card';
    const portrait = document.createElement('span'); portrait.className = 'portrait ' + role; portrait.setAttribute('aria-hidden', 'true');
    const copy = document.createElement('span'); copy.className = 'crew-card-copy';
    const title = document.createElement('strong'); title.textContent = t(role);
    const subtitle = document.createElement('small'); subtitle.textContent = t(role + '_output');
    const arrow = document.createElement('span'); arrow.className = 'crew-arrow'; arrow.textContent = '↗'; arrow.setAttribute('aria-hidden', 'true');
    copy.append(title, subtitle); button.append(portrait, copy, arrow);
    button.onclick = () => { fillAgent(role); $('agent-dialog').showModal(); };
    $('crew-grid').append(button);
  });
}
function fillAgent(role) {
  activeAgent = role;
  $('agent-portrait').className = 'portrait ' + role;
  $('agent-name').textContent = t(role);
  $('agent-description').textContent = t(role + '_description');
  $('agent-output').textContent = t(role + '_output');
}
function renderProjects() {
  $('projects').replaceChildren();
  if (!projects.length) { const p = document.createElement('p'); p.textContent = t('empty'); $('projects').append(p); }
  projects.forEach(p => {
    const button = document.createElement('button');
    button.className = 'project-link' + (p.id === project?.id ? ' active' : '');
    button.textContent = p.title;
    button.onclick = () => { if (!busy && leave()) execute(async () => open(await api(`/api/projects/${p.id}`))); };
    $('projects').append(button);
  });
}
function open(p) {
  project = p;
  selected = Math.max(0, p.steps.findIndex(s => s.status !== 'approved'));
  $('create').hidden = true; $('studio').hidden = false;
  setView(true, false);
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
  $('role-panel-name').textContent = t(step.agent_id);
  $('role-panel-description').textContent = t(step.agent_id + '_description');
  $('role-portrait').className = 'portrait ' + step.agent_id;
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
$('project-form').elements.mode.onchange = event => { $('create-art').src = art(event.target.value); };
$('new').onclick = () => { if (!busy && leave()) newProject(); };
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
document.querySelectorAll('[data-enter-studio]').forEach(a => { a.onclick = event => { event.preventDefault(); enterStudio(a.dataset.mode); }; });
document.querySelectorAll('[data-home]').forEach(a => { a.onclick = event => { event.preventDefault(); goHome(); }; });
document.querySelectorAll('[data-section]').forEach(a => { a.onclick = event => { event.preventDefault(); goHome(a.dataset.section); }; });
document.querySelectorAll('[data-hero-mode]').forEach(button => {
  button.onclick = () => {
    $('hero-art').src = art(button.dataset.heroMode);
    $('project-form').elements.mode.value = button.dataset.heroMode;
    $('create-art').src = art(button.dataset.heroMode);
    document.querySelectorAll('[data-hero-mode]').forEach(b => { const active = b === button; b.classList.toggle('selected', active); b.setAttribute('aria-pressed', String(active)); });
  };
});
$('close-agent').onclick = () => $('agent-dialog').close();
$('agent-dialog').addEventListener('close', () => { activeAgent = null; });
window.addEventListener('popstate', () => { setView(location.pathname === '/studio', false); });
window.addEventListener('beforeunload', event => { if (dirty()) { event.preventDefault(); event.returnValue = ''; } });
localize();
setView(location.pathname === '/studio', false);
execute(async () => { projects = (await api('/api/projects')).projects; renderProjects(); });
