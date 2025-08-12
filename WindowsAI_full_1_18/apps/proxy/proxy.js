import express from 'express';
import fetch from 'node-fetch';
import { createLogger } from '../common/logger.js';

const log = createLogger('proxy');
const PORT = process.env.PROXY_PORT || 15778;
const BIND = process.env.PROXY_BIND || '127.0.0.1';
const OPENAI_KEY = process.env.OPENAI_API_KEY || '';

const app = express();
app.use(express.json({ limit: '4mb' }));

async function probe(url){
  try {
    const ctrl = new AbortController();
    const t = setTimeout(()=>ctrl.abort(), 500);
    const r = await fetch(url, { method:'GET', signal: ctrl.signal });
    clearTimeout(t);
    return r.ok;
  } catch { return false; }
}
async function detectHosts(){
  const ollama = await probe('http://127.0.0.1:11434/');
  const lmstudio = await probe('http://127.0.0.1:1234/');
  return { ollama, lmstudio, openai: !!OPENAI_KEY };
}

app.get('/health', async (req, res) => { res.json({ ok:true, hosts: await detectHosts() }); });

app.get('/v1/models', async (req, res) => {
  const hosts = await detectHosts();
  try {
    if (hosts.lmstudio) {
      const r = await fetch('http://127.0.0.1:1234/v1/models'); const j = await r.json().catch(()=>({data:[]})); return res.json(j);
    }
    if (hosts.ollama) {
      const r = await fetch('http://127.0.0.1:11434/api/tags'); const j = await r.json().catch(()=>({models:[]}));
      const data = (j.models||[]).map(m => ({ id: m.name })); return res.json({ data });
    }
    if (hosts.openai) {
      const r = await fetch('https://api.openai.com/v1/models', { headers:{ Authorization:`Bearer ${OPENAI_KEY}` } }); const j = await r.json().catch(()=>({data:[]})); return res.json(j);
    }
    return res.json({ data: [] });
  } catch (e) { log.error('models_error', { err: String(e) }); return res.status(500).json({ ok:false, error:String(e) }); }
});

app.post('/v1/chat/completions', async (req, res) => {
  const { model, messages, temperature=0.2, max_tokens=512, stream=false } = req.body || {};
  const hosts = await detectHosts();
  try {
    if (hosts.lmstudio) {
      const r = await fetch('http://127.0.0.1:1234/v1/chat/completions', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ model, messages, temperature, max_tokens, stream }) });
      if (stream) { res.status(501).json({ error:'streaming_not_implemented' }); } else { return res.status(r.status).json(await r.json()); }
    }
    if (hosts.ollama) {
      const r = await fetch('http://127.0.0.1:11434/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ model, messages, stream:false, options:{ temperature } }) });
      const j = await r.json();
      const content = j.message && j.message.content ? j.message.content : JSON.stringify(j);
      return res.json({ id:'ollama-chat', choices:[{ index:0, message:{ role:'assistant', content } }], usage:{} });
    }
    if (hosts.openai) {
      const r = await fetch('https://api.openai.com/v1/chat/completions', { method:'POST', headers:{'Content-Type':'application/json', Authorization:`Bearer ${OPENAI_KEY}`}, body: JSON.stringify({ model: model || 'gpt-4o-mini', messages, temperature, max_tokens, stream }) });
      return res.status(r.status).json(await r.json());
    }
    return res.status(503).json({ ok:false, error:'no_model_host_available' });
  } catch (e) { log.error('chat_error', { err:String(e) }); return res.status(500).json({ ok:false, error:String(e) }); }
});

app.listen(PORT, BIND, () => { console.log(`[proxy] http://${BIND}:${PORT}`); });
