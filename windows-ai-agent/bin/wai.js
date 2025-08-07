#!/usr/bin/env node
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);

const [,, cmd, ...rest] = process.argv;

function usage() {
  console.log(`Usage:
wai ask "prompt"
wai sh  "PowerShell-or-bash command"
wai file:read <path>
wai file:write <path> "<content>"
wai gh:dispatch <owner> <repo> <workflow_id> [ref] [jsonInputs]`);
}

const agentPath = path.resolve(__dirname, '..', 'src', 'agent.js');

async function runAgent(args) {
  const child = spawn(process.execPath, [agentPath, '--once', ...args], { stdio: 'inherit' });
  child.on('exit', code => process.exit(code));
}

if (!cmd) { usage(); process.exit(1); }

switch (cmd) {
  case 'ask':
    runAgent(['--job', JSON.stringify({ type:'ask', prompt: rest.join(' ') })]);
    break;
  case 'sh':
    runAgent(['--job', JSON.stringify({ type:'shell', command: rest.join(' ') })]);
    break;
  case 'file:read':
    runAgent(['--job', JSON.stringify({ type:'files.read', path: rest[0] })]);
    break;
  case 'file:write':
    runAgent(['--job', JSON.stringify({ type:'files.write', path: rest[0], content: rest.slice(1).join(' ') })]);
    break;
  case 'gh:dispatch': {
    const [owner, repo, workflow_id, ref='main', inputs='{}'] = rest;
    runAgent(['--job', JSON.stringify({ type:'github.dispatch', owner, repo, workflow_id, ref, inputs: JSON.parse(inputs || '{}') })]);
    break;
  }
  default:
    usage(); process.exit(1);
}
