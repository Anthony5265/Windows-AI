import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';
import path from 'path';
import { detectPython } from './_util.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');

const python = detectPython();
const extraArgs = process.argv.slice(2);
const pytestArgs = [...python.args, '-m', 'pytest', ...extraArgs];

const result = spawnSync(python.cmd, pytestArgs, {
  cwd: repoRoot,
  stdio: 'inherit'
});

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

if (typeof result.status === 'number') {
  process.exit(result.status);
}

process.exit(1);
