import fs from 'fs';
import path from 'path';
import os from 'os';

function ensureDir(p){ if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true }); }
const levelOrder = { error:0, warn:1, info:2, debug:3 };

function currentLevel(){
  try {
    const pd = process.env.PROGRAMDATA || 'C:\\ProgramData';
    const cfgp = path.join(pd, 'Windows AI', 'config', 'defaults.json');
    const raw = fs.existsSync(cfgp) ? JSON.parse(fs.readFileSync(cfgp,'utf8')) : {};
    const lvl = (((raw.logs||{}).level) || 'info').toLowerCase();
    return levelOrder[lvl] ?? 2;
  } catch { return 2; }
}

export function createLogger(serviceName){
  const base = process.env.WINAI_LOG_DIR || path.join(process.env.PROGRAMDATA || 'C:\\ProgramData', 'Windows AI', 'logs');
  ensureDir(base);
  function log(level, msg, meta={}){
    if ((levelOrder[level] ?? 2) > currentLevel()) return;
    const day = new Date().toISOString().slice(0,10);
    const file = path.join(base, `${serviceName}-${day}.jsonl`);
    const rec = { t: new Date().toISOString(), level, msg, ...meta };
    fs.appendFile(file, JSON.stringify(rec) + os.EOL, ()=>{});
    if (process.env.NODE_ENV !== 'production') console.log(`[${serviceName}]`, level, msg, meta);
  }
  return {
    info: (m,meta)=>log('info',m,meta),
    warn: (m,meta)=>log('warn',m,meta),
    error: (m,meta)=>log('error',m,meta),
    debug: (m,meta)=>log('debug',m,meta),
  };
}
