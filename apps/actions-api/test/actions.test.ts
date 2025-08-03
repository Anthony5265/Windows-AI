import { test } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs/promises';
import path from 'node:path';
import { executeAction } from '../src/actions';

test('shell executes command', async () => {
  const result = await executeAction({ action: 'shell', params: { command: 'echo hello' } });
  assert.strictEqual(result.stdout.trim(), 'hello');
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
