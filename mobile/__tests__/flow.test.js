const { loginRequest, pairRequest } = require('../api');

describe('login and pairing flow', () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  test('successful login followed by pairing', async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ token: 'tok123' }) });

    await expect(loginRequest('user', 'pass')).resolves.toBe(true);
    await expect(pairRequest('device1')).resolves.toBe('tok123');

    expect(fetch).toHaveBeenNthCalledWith(1, 'https://example.com/api/login', expect.any(Object));
    expect(fetch).toHaveBeenNthCalledWith(2, 'https://example.com/api/pair', expect.any(Object));
  });

  test('handles errors in flow', async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: false });
    await expect(loginRequest('user', 'pass')).rejects.toThrow('Login failed');
  });
});
