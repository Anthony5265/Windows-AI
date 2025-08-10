const { loginRequest, pairRequest } = require('../api');

describe('loginRequest', () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  test('resolves on successful login', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({})
    });
    await expect(loginRequest('user', 'pass')).resolves.toBe(true);
    expect(fetch).toHaveBeenCalledWith('https://example.com/api/login', expect.any(Object));
  });

  test('throws on login failure', async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: false });
    await expect(loginRequest('user', 'pass')).rejects.toThrow('Login failed');
  });
});

describe('pairRequest', () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  test('returns token on success', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ token: 'tok123' })
    });
    await expect(pairRequest('device1')).resolves.toBe('tok123');
    expect(fetch).toHaveBeenCalledWith('https://example.com/api/pair', expect.any(Object));
  });

  test('throws on failure', async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: false });
    await expect(pairRequest('device1')).rejects.toThrow('Pairing failed');
  });
});
