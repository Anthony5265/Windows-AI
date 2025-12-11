/**
 * Settings Panel Component
 * 
 * Provides UI for managing:
 * - API keys for various AI services
 * - Model selection and configuration
 * - System preferences
 * - Plugin settings
 * - Health monitoring
 */

class SettingsPanel {
    constructor() {
        this.apiEndpoint = 'http://127.0.0.1:8010';
        this.currentCategory = 'api-keys';
        this.apiKeys = {};
        this.systemConfig = {};
        this.healthData = {};
        
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        await this.loadSettings();
        await this.loadHealthStatus();
        
        // Start health monitoring
        setInterval(() => this.loadHealthStatus(), 30000); // Every 30 seconds
    }
    
    setupEventListeners() {
        // Category navigation
        document.querySelectorAll('.settings-category-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchCategory(e.target.dataset.category);
            });
        });
        
        // API key management
        document.getElementById('saveApiKeysBtn')?.addEventListener('click', () => {
            this.saveApiKeys();
        });
        
        document.getElementById('testApiKeyBtn')?.addEventListener('click', () => {
            this.testApiKey();
        });
        
        // Model configuration
        document.getElementById('saveModelConfigBtn')?.addEventListener('click', () => {
            this.saveModelConfig();
        });
        
        // System preferences
        document.getElementById('savePreferencesBtn')?.addEventListener('click', () => {
            this.savePreferences();
        });
        
        // Health monitoring
        document.getElementById('refreshHealthBtn')?.addEventListener('click', () => {
            this.loadHealthStatus();
        });
        
        document.getElementById('viewLogsBtn')?.addEventListener('click', () => {
            this.openLogViewer();
        });
    }
    
    switchCategory(category) {
        this.currentCategory = category;
        
        // Update navigation
        document.querySelectorAll('.settings-category-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.category === category);
        });
        
        // Show selected section
        document.querySelectorAll('.settings-section').forEach(section => {
            section.classList.toggle('active', section.id === `${category}-section`);
        });
    }
    
    async loadSettings() {
        try {
            // Load API keys
            const apiKeysResponse = await fetch(`${this.apiEndpoint}/api/setup/api-keys`);
            if (apiKeysResponse.ok) {
                const data = await apiKeysResponse.json();
                this.apiKeys = data.api_keys || {};
                this.renderApiKeys();
            }
            
            // Load system configuration
            const configResponse = await fetch(`${this.apiEndpoint}/api/config`);
            if (configResponse.ok) {
                this.systemConfig = await configResponse.json();
                this.renderSystemConfig();
            }
            // Load available models from backend
            try {
                const modelsRes = await fetch(`${this.apiEndpoint}/models`);
                if (modelsRes.ok) {
                    const json = await modelsRes.json();
                    this.systemConfig.available_models = json.models || json;
                    this.renderSystemConfig();
                }
            } catch (err) {
                console.warn('Failed to load available models', err);
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
            this.showError('Failed to load settings. Please check your connection.');
        }
    }
    
    renderApiKeys() {
        const container = document.getElementById('apiKeysContainer');
        if (!container) return;
        
        const services = [
            { id: 'openai', name: 'OpenAI', description: 'GPT-4, GPT-3.5, DALL-E' },
            { id: 'anthropic', name: 'Anthropic', description: 'Claude models' },
            { id: 'google', name: 'Google AI', description: 'Gemini, PaLM' },
            { id: 'cohere', name: 'Cohere', description: 'Command, Embed models' },
            { id: 'azure_openai', name: 'Azure OpenAI', description: 'Enterprise OpenAI' },
            { id: 'huggingface', name: 'Hugging Face', description: 'Open source models' }
        ];
        
        container.innerHTML = services.map(service => `
            <div class="api-key-item">
                <div class="api-key-header">
                    <div>
                        <h4>${service.name}</h4>
                        <p class="api-key-description">${service.description}</p>
                    </div>
                    <span class="api-key-status ${this.apiKeys[service.id] ? 'active' : 'inactive'}">
                        ${this.apiKeys[service.id] ? '✓ Configured' : '○ Not configured'}
                    </span>
                </div>
                <div class="api-key-form">
                    <input 
                        type="password" 
                        id="apiKey_${service.id}"
                        class="api-key-input"
                        placeholder="Enter ${service.name} API key"
                        value="${this.apiKeys[service.id] ? '••••••••••••••••' : ''}"
                    />
                    <button 
                        class="btn-secondary"
                        onclick="settingsPanel.toggleApiKeyVisibility('${service.id}')"
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                            <circle cx="12" cy="12" r="3"/>
                        </svg>
                    </button>
                    ${this.apiKeys[service.id] ? `
                        <button 
                            class="btn-danger"
                            onclick="settingsPanel.deleteApiKey('${service.id}')"
                        >
                            Delete
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }
    
    toggleApiKeyVisibility(serviceId) {
        const input = document.getElementById(`apiKey_${serviceId}`);
        if (!input) return;
        
        input.type = input.type === 'password' ? 'text' : 'password';
    }
    
    async saveApiKeys() {
        const services = ['openai', 'anthropic', 'google', 'cohere', 'azure_openai', 'huggingface'];
        const updates = [];
        
        for (const service of services) {
            const input = document.getElementById(`apiKey_${service}`);
            if (!input || !input.value || input.value.startsWith('••••')) continue;
            
            updates.push(
                fetch(`${this.apiEndpoint}/api/setup/api-key`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        service: service,
                        api_key: input.value
                    })
                })
            );
        }
        
        try {
            await Promise.all(updates);
            this.showSuccess('API keys saved successfully');
            await this.loadSettings();
        } catch (error) {
            console.error('Failed to save API keys:', error);
            this.showError('Failed to save API keys');
        }
    }
    
    async deleteApiKey(serviceId) {
        if (!confirm(`Delete API key for ${serviceId}?`)) return;
        
        try {
            const response = await fetch(`${this.apiEndpoint}/api/setup/api-key/${serviceId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showSuccess('API key deleted');
                await this.loadSettings();
            } else {
                throw new Error('Delete failed');
            }
        } catch (error) {
            console.error('Failed to delete API key:', error);
            this.showError('Failed to delete API key');
        }
    }
    
    async testApiKey() {
        const service = document.getElementById('testApiKeyService')?.value;
        if (!service) return;
        
        const testBtn = document.getElementById('testApiKeyBtn');
        testBtn.disabled = true;
        testBtn.textContent = 'Testing...';
        
        try {
            const response = await fetch(`${this.apiEndpoint}/api/test-connection`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ service })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess(`${service} connection successful`);
            } else {
                this.showError(`${service} connection failed: ${result.error}`);
            }
        } catch (error) {
            console.error('Connection test failed:', error);
            this.showError('Connection test failed');
        } finally {
            testBtn.disabled = false;
            testBtn.textContent = 'Test Connection';
        }
    }
    
    renderSystemConfig() {
        // Model configuration
        const modelSelect = document.getElementById('defaultModelSelect');
        if (modelSelect && this.systemConfig.available_models) {
            modelSelect.innerHTML = this.systemConfig.available_models.map(model => `
                <option value="${model.id}" ${model.id === this.systemConfig.default_model ? 'selected' : ''}>
                    ${model.name} - ${model.provider}
                </option>
            `).join('');
        }
        
        // System preferences
        if (this.systemConfig.preferences) {
            const prefs = this.systemConfig.preferences;
            
            document.getElementById('autoStartEnabled').checked = prefs.auto_start || false;
            document.getElementById('minimizeToTray').checked = prefs.minimize_to_tray !== false;
            document.getElementById('notificationsEnabled').checked = prefs.notifications !== false;
            document.getElementById('telemetryEnabled').checked = prefs.telemetry || false;
            document.getElementById('maxTokens').value = prefs.max_tokens || 2048;
            document.getElementById('temperature').value = prefs.temperature || 0.7;
        }
    }
    
    async saveModelConfig() {
        const config = {
            default_model: document.getElementById('defaultModelSelect')?.value,
            max_tokens: parseInt(document.getElementById('maxTokens')?.value || '2048'),
            temperature: parseFloat(document.getElementById('temperature')?.value || '0.7')
        };
        
        try {
            const response = await fetch(`${this.apiEndpoint}/api/config/model`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            if (response.ok) {
                this.showSuccess('Model configuration saved');
                await this.loadSettings();
            } else {
                throw new Error('Save failed');
            }
        } catch (error) {
            console.error('Failed to save model config:', error);
            this.showError('Failed to save model configuration');
        }
    }
    
    async savePreferences() {
        const preferences = {
            auto_start: document.getElementById('autoStartEnabled')?.checked,
            minimize_to_tray: document.getElementById('minimizeToTray')?.checked,
            notifications: document.getElementById('notificationsEnabled')?.checked,
            telemetry: document.getElementById('telemetryEnabled')?.checked
        };
        
        try {
            const response = await fetch(`${this.apiEndpoint}/api/config/preferences`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(preferences)
            });
            
            if (response.ok) {
                this.showSuccess('Preferences saved');
            } else {
                throw new Error('Save failed');
            }
        } catch (error) {
            console.error('Failed to save preferences:', error);
            this.showError('Failed to save preferences');
        }
    }
    
    async loadHealthStatus() {
        try {
            const response = await fetch(`${this.apiEndpoint}/api/health/`);
            if (!response.ok) throw new Error('Health check failed');
            
            this.healthData = await response.json();
            this.renderHealthStatus();
        } catch (error) {
            console.error('Failed to load health status:', error);
            this.renderHealthError();
        }
    }
    
    renderHealthStatus() {
        const container = document.getElementById('healthStatusContainer');
        if (!container) return;
        
        const { status, components } = this.healthData;
        
        container.innerHTML = `
            <div class="health-overview ${status}">
                <h3>System Status: ${status.toUpperCase()}</h3>
                <p class="health-timestamp">Last checked: ${new Date().toLocaleString()}</p>
            </div>
            
            <div class="health-components">
                ${Object.entries(components || {}).map(([name, data]) => `
                    <div class="health-component ${data.status}">
                        <div class="health-component-header">
                            <h4>${name}</h4>
                            <span class="health-status-badge ${data.status}">
                                ${data.status === 'healthy' ? '✓' : '✗'} ${data.status}
                            </span>
                        </div>
                        ${data.message ? `<p class="health-message">${data.message}</p>` : ''}
                        ${data.details ? `
                            <div class="health-details">
                                ${Object.entries(data.details).map(([key, value]) => `
                                    <div class="health-detail-item">
                                        <span class="health-detail-key">${key}:</span>
                                        <span class="health-detail-value">${value}</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    renderHealthError() {
        const container = document.getElementById('healthStatusContainer');
        if (!container) return;
        
        container.innerHTML = `
            <div class="health-overview error">
                <h3>⚠️ Unable to Connect to Backend</h3>
                <p>Please ensure the Windows AI backend is running.</p>
                <button onclick="settingsPanel.loadHealthStatus()" class="btn-primary">
                    Retry
                </button>
            </div>
        `;
    }
    
    async openLogViewer() {
        try {
            const response = await fetch(`${this.apiEndpoint}/api/health/logs/recent?limit=100`);
            if (!response.ok) throw new Error('Failed to fetch logs');
            
            const logs = await response.json();
            this.showLogViewerModal(logs);
        } catch (error) {
            console.error('Failed to load logs:', error);
            this.showError('Failed to load logs');
        }
    }
    
    showLogViewerModal(logs) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content log-viewer-modal">
                <div class="modal-header">
                    <h3>System Logs</h3>
                    <button onclick="this.closest('.modal-overlay').remove()" class="modal-close">×</button>
                </div>
                <div class="modal-body">
                    <div class="log-filters">
                        <select id="logLevelFilter" onchange="settingsPanel.filterLogs()">
                            <option value="all">All Levels</option>
                            <option value="ERROR">Errors Only</option>
                            <option value="WARNING">Warnings+</option>
                            <option value="INFO">Info+</option>
                        </select>
                    </div>
                    <div class="log-entries">
                        ${logs.map(log => `
                            <div class="log-entry log-${log.level.toLowerCase()}">
                                <span class="log-timestamp">${log.timestamp}</span>
                                <span class="log-level">${log.level}</span>
                                <span class="log-message">${log.message}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize settings panel when loaded
let settingsPanel;
document.addEventListener('DOMContentLoaded', () => {
    settingsPanel = new SettingsPanel();
});
