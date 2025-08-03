import express from 'express';
import { executeAction } from './actions';

const app = express();
app.use(express.json());

app.post('/api/actions/execute', async (req, res) => {
  try {
    const result = await executeAction(req.body);
    res.json({ ok: true, result });
  } catch (err: any) {
    console.error(JSON.stringify({ level: 'error', message: err.message }));
    res.status(400).json({ ok: false, error: { message: err.message } });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(JSON.stringify({ level: 'info', message: 'actions api listening', port }));
});
