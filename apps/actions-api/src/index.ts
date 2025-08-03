import express from 'express';
import { executeAction } from './actions';
import { normalize } from './normalize';
import { ValidationError } from './errors';

export const app = express();
app.use(express.json());

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
        JSON.stringify({
          level: 'error',
          message: err.message,
          stack: err.stack
        })
      );
      res.status(500).json({ ok: false, error: { message: 'Internal server error' } });
    }
  }
});

if (require.main === module) {
  const port = process.env.PORT || 3000;
  app.listen(port, () => {
    console.log(
      JSON.stringify({ level: 'info', message: 'actions api listening', port })
    );
  });
}
