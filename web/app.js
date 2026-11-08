const byId = (id) => document.getElementById(id);
const names = {search:'Search the repository',read_symbol:'Read the symbol',apply_patch:'Apply the patch',run_tests:'Run the tests',finish:'Write the receipt'};
let current;
function number(value) {return Number.isFinite(value) && value >= 0 ? value : 0;}
function selectStep(index) {
  const step = current.steps[index];
  document.querySelectorAll('.step').forEach((button, i) => button.setAttribute('aria-pressed', String(i === index)));
  byId('step-name').textContent = `${String(index+1).padStart(2,'0')} / ${step.action || 'model call'}`;
  byId('step-usage').textContent = `${number(step.tokens_in).toLocaleString()} in · ${number(step.tokens_out).toLocaleString()} out`;
  const args = step.args ? JSON.stringify(step.args, null, 2) : '';
  byId('step-content').textContent = [args, step.result || step.error || (step.action === 'finish' ? current.summary : '')].filter(Boolean).join('\n\n');
}
function render(record) {
  if (!record || !Array.isArray(record.steps) || record.steps.length > 500 || !record.totals || typeof record.task !== 'string') throw new Error('Choose a Penny run.json containing task, totals and steps.');
  current = record;
  const mock = Boolean(record.flags?.mock);
  byId('mode').textContent = mock ? 'MOCK' : 'IMPORTED RECORD';
  byId('mode').classList.toggle('mock', mock);
  byId('record-label').textContent = mock ? 'RECORDED MOCK RUN' : 'YOUR LOCAL RECORD';
  byId('task').textContent = record.task;
  byId('tokens').textContent = `${(number(record.totals.tokens_in)+number(record.totals.tokens_out)).toLocaleString()} tokens`;
  byId('cost').textContent = record.totals.cost_usd == null ? 'price not configured' : `$${number(record.totals.cost_usd).toFixed(6)} · recorded cost`;
  byId('status').textContent = String(record.status || 'recorded').toUpperCase();
  const tests = Array.isArray(record.tests) ? record.tests : [];
  byId('test-summary').textContent = `${record.steps.length} steps · ${tests.filter(t=>t.returncode === 0).length}/${tests.length} test commands passed`;
  byId('viewer-note').textContent = mock ? 'MOCK: scripted model actions and synthetic usage. Filesystem edits and tests were executed. This viewer does not call a model.' : 'Imported data is displayed as provided; this viewer does not independently verify it. Your JSON stays in this browser.';
  byId('steps').replaceChildren();
  record.steps.forEach((step, index) => {
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'step';
    const counter = document.createElement('span'); counter.textContent = String(index+1).padStart(2,'0');
    const label = document.createTextNode(names[step.action] || String(step.action || 'Model call'));
    button.append(counter,label);button.addEventListener('click',()=>selectStep(index));byId('steps').append(button);
  });
  if(record.steps.length) selectStep(Math.min(2,record.steps.length-1));
  else {byId('step-name').textContent='NO MODEL STEPS';byId('step-content').textContent=record.error || 'This record contains no model steps.';byId('step-usage').textContent='';}
}
fetch('demo.json').then(r=>{if(!r.ok)throw new Error('The bundled demo could not load.');return r.json();}).then(render).catch(error=>byId('error').textContent=error.message);
byId('record-file').addEventListener('change',async(event)=>{
  const file=event.target.files[0];if(!file)return;
  try {if(file.size>5_000_000)throw new Error('Choose a run record smaller than 5 MB.');render(JSON.parse(await file.text()));byId('error').textContent='';}
  catch(error){byId('error').textContent=error.message;}
});
byId('copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(byId('install').textContent);byId('copy').textContent='Copied';}catch{byId('copy').textContent='Select commands';}});
