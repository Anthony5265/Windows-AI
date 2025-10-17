import { spawnSync } from 'child_process';
export function detectPython(){
  const candidates = [
    {cmd:'python', args:['--version']},
    {cmd:'python3', args:['--version']},
    {cmd:'py', args:['-3','--version']},
  ];
  for (const c of candidates){
    const r = spawnSync(c.cmd, c.args, {encoding:'utf8'});
    if (r.status === 0 || (r.stdout && r.stdout.includes('Python')) || (r.stderr && r.stderr.includes('Python'))) {
      return { cmd: c.cmd, args: [] };
    }
  }
  return { cmd: 'python', args: [] };
}
