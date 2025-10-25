import OpenAI from 'openai';

function client() {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error('Missing OPENAI_API_KEY environment variable');
  }
  return new OpenAI({ apiKey });
}

export async function ask(prompt) {
  const c = client();
  const res = await c.responses.create({
    model: 'gpt-4.1-nano',
    input: prompt
  });
  return res.output_text ?? JSON.stringify(res);
}
