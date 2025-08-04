import { test } from 'node:test';
import assert from 'node:assert';
import { app } from '../src/index';

async function startServer() {
  const server = app.listen(0);
  await new Promise<void>((resolve) => server.once('listening', () => resolve()));
  const address = server.address();
  if (typeof address === 'string' || !address) {
    throw new Error('Failed to get server address');
  }
  return { server, port: address.port };
}

test('mesh distribute echoes task', async () => {
  const { server, port } = await startServer();
  const res = await fetch(`http://localhost:${port}/api/mesh/distribute`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ task: 'compute' })
  });
  assert.strictEqual(res.status, 200);
  const body = await res.json();
  assert.strictEqual(body.ok, true);
  assert.strictEqual(body.result.distributed, 'compute');
  await new Promise((resolve) => server.close(resolve));
});
