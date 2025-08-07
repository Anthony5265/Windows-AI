import fs from 'fs/promises';

export async function read(p){
  const data = await fs.readFile(p, 'utf-8');
  return { status:'ok', path:p, size:data.length, preview:data.slice(0,1000) };
}

export async function write(p, content){
  await fs.writeFile(p, content, 'utf-8');
  return { status:'ok', path:p, bytes: Buffer.from(content,'utf-8').length };
}
