/* Windows AI - Actions API (expanded) */
import express from 'express';
import os from 'os';
import fs from 'fs';
import path from 'path';
import child_process from 'child_process';
import { createLogger } from '../common/logger.js';

const log = createLogger('actions');
const PORT = process.env.ACTIONS_PORT || 15770;
const BIND = process.env.ACTIONS_BIND || '127.0.0.1';
const TOKEN = process.env.ACTIONS_TOKEN || '';

const app = express();
app.use(express.json({ limit: '2mb' }));

function ok(res, body={}) { res.json({ ok: true, ...body }); }
function version() { return { name: 'actions', version: '0.2.0', build: 1 }; }

function auth(req, res, next){
  if (!TOKEN) return next(); // local-only default
  const h = req.headers['x-winai-token'];
  if (h !== TOKEN) return res.status(401).json({ ok:false, error:'unauthorized' });
  next();
}
function allowlist() {
  try {
    const pd = process.env.PROGRAMDATA || 'C:\\ProgramData';
    const override = path.join(pd, 'Windows AI', 'config', 'actions-permissions.json');
    if (fs.existsSync(override)) { const raw = JSON.parse(fs.readFileSync(override, 'utf8')); return new Set(raw.allowed || []); }
  } catch {}
  return new Set(['system.info','files.list','files.read','files.write','echo','process.list','process.kill','shell.run','registry.get','registry.set']);
}
const ALLOWED = allowlist();

app.get('/health', (req, res) => ok(res));
app.get('/version', (req, res) => res.json(version()));

// Utilities
function safePath(p){ const home = os.homedir().replace(/\\/g,'/'); return p && p.startsWith(home); }

app.post('/api/actions/execute', auth, async (req, res) => {
  const { action, params } = req.body || {};
  if (!ALLOWED.has(action)) { log.warn('blocked_action', { action }); return res.status(400).json({ ok:false, error:'action_not_allowed' }); }
  try {
    switch(action){
      case 'system.info': {
        const result = { platform: os.platform(), arch: os.arch(), cpus: os.cpus().length, totalmem: os.totalmem() };
        log.info('system.info', { result }); return ok(res, { result });
      }
      case 'files.list': {
        const p = params?.path || os.homedir();
        const entries = fs.readdirSync(p).slice(0, 500);
        log.info('files.list', { path: p, count: entries.length }); return ok(res, { result: entries });
      }
      case 'files.read': {
        const p = params?.path; if (!p || !safePath(p)) return res.status(400).json({ ok:false, error:'path_not_allowed' });
        const data = fs.readFileSync(p, 'utf8'); return ok(res, { result: data });
      }
      case 'files.write': {
        const p = params?.path; const data = params?.data ?? '';
        if (!p || !safePath(p)) return res.status(400).json({ ok:false, error:'path_not_allowed' });
        fs.writeFileSync(p, data, 'utf8'); return ok(res, { result: 'written' });
      }
      case 'process.list': {
        const out = child_process.execSync('wmic process get ProcessId,Name,WorkingSetSize /FORMAT:CSV', { encoding:'utf8' });
        return ok(res, { result: out });
      }
      case 'process.kill': {
        const pid = Number(params?.pid); if (!pid || pid < 100) return res.status(400).json({ ok:false, error:'invalid_pid' });
        child_process.execSync(`taskkill /PID ${pid} /F`); return ok(res, { result: 'killed' });
      }
      case 'shell.run': {
        const cmd = params?.command; if (!cmd) return res.status(400).json({ ok:false, error:'missing_command' });
        if (/rm -rf|format|shutdown|bcdedit/i.test(cmd)) return res.status(400).json({ ok:false, error:'dangerous_command_blocked' });
        const out = child_process.execSync(cmd, { encoding:'utf8', windowsHide:true });
        return ok(res, { result: out });
      }
      case 'registry.get': {
        const key = params?.key; if (!key) return res.status(400).json({ ok:false, error:'missing_key' });
        const out = child_process.execSync(`reg query "${key}"`, { encoding:'utf8' });
        return ok(res, { result: out });
      }
      case 'registry.set': {
        const key = params?.key; const name = params?.name || ''; const type = params?.type || 'REG_SZ'; const val = params?.value || '';
        if (!key) return res.status(400).json({ ok:false, error:'missing_key' });
        child_process.execSync(`reg add "${key}" /v "${name}" /t ${type} /d "${val}" /f`, { encoding:'utf8' });
        return ok(res, { result: 'ok' });
      }
      case 'echo': return ok(res, { result: params || {} });
      default: return res.status(400).json({ ok:false, error:'unhandled' });
    }
  } catch (e) {
    log.error('action_error', { action, err: String(e) }); return res.status(500).json({ ok:false, error:String(e) });
  }
});
app.listen(PORT, BIND, () => { log.info('listening', { url: `http://${BIND}:${PORT}` }); console.log(`[actions] http://${BIND}:${PORT}`); });
