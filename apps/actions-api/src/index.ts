import express from 'express';
import { executeAction } from './actions';
import { normalize } from './normalize';
import { ValidationError } from './errors';
import { createPairingToken, handleRemoteCommand } from './mobile';
import { distributeTask } from './mesh';
import { handleDeviceEvent } from './iot';
import { searchDocuments } from './search';

export const app = express();
app.use(express.json());

app.post('/api/mobile/pair', (req, res) => {
  try {
    const token = createPairingToken(req.body.deviceId);
    res.json({ ok: true, token });
  } catch (err: any) {
    if (err instanceof ValidationError) {
      res.status(400).json({ ok: false, error: { message: err.message } });
    } else {
      console.error(
        JSON.stringify({ level: 'error', message: err.message, stack: err.stack })
      );
      res.status(500).json({ ok: false, error: { message: 'Internal server error' } });
    }
  }
});

app.post('/api/mobile/command', async (req, res) => {
  try {
    const { token, ...body } = req.body;
    const result = await handleRemoteCommand(token, body);
    res.json({ ok: true, result });
  } catch (err: any) {
    if (err instanceof ValidationError) {
      res.status(400).json({ ok: false, error: { message: err.message } });
    } else {
      console.error(
        JSON.stringify({ level: 'error', message: err.message, stack: err.stack })
      );
      res.status(500).json({ ok: false, error: { message: 'Internal server error' } });
    }
  }
});

app.post('/api/actions/execute', async (req, res) => {
  try {
    const norm = normalize(req.body);
    const result = await executeAction(norm);
    res.json({ ok: true, result });
  } catch (err: any) {
    if (err instanceof ValidationError) {
      res.status(400).json({ ok: false, error: { message: err.message } });
    } else {
      console.error(
        JSON.stringify({ level: 'error', message: err.message, stack: err.stack })
      );
      res.status(500).json({ ok: false, error: { message: 'Internal server error' } });
    }
  }
});

app.post('/api/mesh/distribute', (req, res) => {
  try {
    const result = distributeTask(req.body);
    res.json({ ok: true, result });
  } catch (err: any) {
    if (err instanceof ValidationError) {
      res.status(400).json({ ok: false, error: { message: err.message } });
    } else {
      console.error(
        JSON.stringify({ level: 'error', message: err.message, stack: err.stack })
      );
      res.status(500).json({ ok: false, error: { message: 'Internal server error' } });
    }
  }
});

app.post('/api/iot/event', (req, res) => {
  try {
    const result = handleDeviceEvent(req.body);
    res.json({ ok: true, result });
  } catch (err: any) {
    if (err instanceof ValidationError) {
      res.status(400).json({ ok: false, error: { message: err.message } });
    } else {
      console.error(
        JSON.stringify({ level: 'error', message: err.message, stack: err.stack })
      );
      res.status(500).json({ ok: false, error: { message: 'Internal server error' } });
    }
  }
});

app.post('/api/search/query', (req, res) => {
  try {
    const result = searchDocuments(req.body);
    res.json({ ok: true, result });
  } catch (err: any) {
    if (err instanceof ValidationError) {
      res.status(400).json({ ok: false, error: { message: err.message } });
    } else {
      console.error(
        JSON.stringify({ level: 'error', message: err.message, stack: err.stack })
      );
      res.status(500).json({ ok: false, error: { message: 'Internal server error' } });
    }
  }
});

if (require.main === module) {
  const port = process.env.PORT || 3000;
  app.listen(port, () => {
    console.log(JSON.stringify({ level: 'info', message: 'actions api listening', port }));
  });
}
