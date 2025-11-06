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
  try {
    const res = await c.chat.completions.create({
      model: 'gpt-3.5-turbo', // Use valid model name
      messages: [
        { role: 'system', content: 'You are a helpful assistant.' },
        { role: 'user', content: prompt }
      ]
    });
    return res.choices?.[0]?.message?.content ?? JSON.stringify(res);
  } catch (error) {
    throw new Error(`OpenAI API error: ${error.message}`);
  }
}
