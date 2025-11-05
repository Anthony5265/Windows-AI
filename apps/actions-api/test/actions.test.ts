import { test } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs/promises';
import path from 'node:path';
import { executeAction } from '../src/actions.js';

test('shell executes command', async () => {
  const result = await executeAction({ action: 'shell', params: { command: 'echo hello' } });
  assert.strictEqual(result.stdout.trim(), 'hello');
});

test('shell runs platform-specific list command', async () => {
  const cmd = process.platform === 'win32' ? 'dir' : 'ls';
  const result = await executeAction({ action: 'shell', params: { command: cmd } });
  assert.ok(result.stdout.toLowerCase().includes('package.json'));
});

test('shell prints file contents', async () => {
  const cmd = process.platform === 'win32' ? 'type package.json' : 'cat package.json';
  const result = await executeAction({ action: 'shell', params: { command: cmd } });
  assert.ok(result.stdout.includes('"name"'));
});

test('shell rejects command with disallowed characters', async () => {
  await assert.rejects(
    executeAction({ action: 'shell', params: { command: 'echo hello; ls' } })
  );
});

test('shell rejects command not in whitelist', async () => {
  await assert.rejects(
    executeAction({ action: 'shell', params: { command: 'rm -rf /' } })
  );
});

test('shell rejects command with pipe', async () => {
  await assert.rejects(
    executeAction({ action: 'shell', params: { command: 'ls | cat' } })
  );
});

test('write_file and read_file', async () => {
  const tmp = path.join(process.cwd(), 'tmp.txt');
  await executeAction({ action: 'write_file', params: { path: tmp, content: 'hi' } });
  const res = await executeAction({ action: 'read_file', params: { path: tmp } });
  assert.strictEqual(res.content, 'hi');
  await fs.unlink(tmp);
});

test('get_system_info returns fields', async () => {
  const res = await executeAction({ action: 'get_system_info' });
  assert.ok(res.platform);
  assert.ok(res.arch);
});

