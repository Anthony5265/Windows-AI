// Basic tabs
const tabs = document.querySelectorAll('nav button');
const sections = document.querySelectorAll('.tab');
tabs.forEach(btn => btn.addEventListener('click', () => { sections.forEach(s => s.classList.remove('active')); document.getElementById(btn.dataset.tab).classList.add('active'); }));

(async ()=>{
  const env = await window.winAI.envInfo();
  document.getElementById('env').textContent = `Env: ${env.platform}/${env.arch} Electron ${env.versions.electron}`;

  // Config controls
  const cfg = await window.winAI.readConfig();
  document.getElementById('bind').value = cfg?.network?.bind || '127.0.0.1';
  document.getElementById('theme').value = cfg?.ui?.theme || 'system';
  document.getElementById('saveCfg').onclick = async ()=>{
    const next = cfg || {};
    next.network = next.network || {}; next.ui = next.ui || {};
    next.network.bind = document.getElementById('bind').value;
    next.ui.theme = document.getElementById('theme').value;
    await window.winAI.writeConfig(next);
    alert('Saved.');
  };

  // Workflow runner
  document.getElementById('runEcho').onclick = async ()=>{
    const res = await fetch('http://127.0.0.1:15777/workflows/run', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ name:'echo', inputs:{} }) });
    const j = await res.json(); document.getElementById('wfOut').textContent = JSON.stringify(j, null, 2);
  };
})(); 
