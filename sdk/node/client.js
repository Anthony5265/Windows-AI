export class WindowsAIClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  async _post(path, body) {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    const data = await res.json();
    return data.result ?? data.token;
  }

  executeAction(action, params = {}) {
    return this._post('/api/actions/execute', { action, params });
  }

  mobilePair(deviceId) {
    return this._post('/api/mobile/pair', { deviceId });
  }

  mobileCommand(token, action, params = {}) {
    return this._post('/api/mobile/command', { token, action, params });
  }

  meshDistribute(task) {
    return this._post('/api/mesh/distribute', { task });
  }

  iotEvent(deviceId, event) {
    return this._post('/api/iot/event', { deviceId, event });
  }

  searchQuery(query, documents = {}) {
    return this._post('/api/search/query', { query, documents });
  }
}
