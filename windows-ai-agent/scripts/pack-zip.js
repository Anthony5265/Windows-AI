import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const root = path.resolve(__dirname, '..');
const outDir = path.join(root, 'dist');
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir);

console.log('Installing deps (production)…');
execSync('npm ci --omit=dev', { cwd: root, stdio:'inherit' });

const zipName = `windows-ai-agent.zip`;
const zipPath = path.join(outDir, zipName);
if (fs.existsSync(zipPath)) fs.unlinkSync(zipPath);

// Use system zip where available
execSync(`zip -r ${zipPath} . -x "dist/*"`, { cwd: root, stdio:'inherit', shell:true });
console.log('Packed:', zipPath);
