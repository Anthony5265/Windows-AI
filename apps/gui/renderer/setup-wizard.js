/**
 * Windows AI - First Run Setup Wizard
 * Guides users through initial configuration
 */

class SetupWizard {
    constructor() {
        this.apiEndpoint = 'http://127.0.0.1:8010';
        this.currentStep = 1;
        this.totalSteps = 4;
        this.setupData = {
            apiKeys: {},
            selectedModel: null,
            preferences: {},
            providerSetup: null,
        };
        this.initialized = false;
    }

    /**
     * Initialize the setup wizard
     */
    async init() {
        // Check if setup is needed
        const setupNeeded = await this.checkSetupRequired();
        
        if (setupNeeded) {
            this.show();
        }
        
        this.initialized = true;
        return setupNeeded;
    }

    /**
     * Check if initial setup is required
     */
    async checkSetupRequired() {
        try {
            const response = await fetch(`${this.apiEndpoint}/api/setup/status`);
            if (response.ok) {
                const status = await response.json();
                // Backend returns is_complete field
                return !status.is_complete;
            }
        } catch (error) {
            console.error('Failed to check setup status:', error);
            // If backend is not available, might still need setup
            return true;
        }
        return true;
    }

    /**
     * Show the setup wizard
     */
    show() {
        // Create wizard overlay if it doesn't exist
        if (!document.getElementById('setupWizardOverlay')) {
            this.createWizardUI();
        }

        const overlay = document.getElementById('setupWizardOverlay');
        overlay.style.display = 'flex';
        
        // Show first step
        this.goToStep(1);
    }

    /**
     * Hide the setup wizard
     */
    hide() {
        const overlay = document.getElementById('setupWizardOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    /**
     * Create the wizard UI elements
     */
    createWizardUI() {
        const overlay = document.createElement('div');
        overlay.id = 'setupWizardOverlay';
        overlay.className = 'setup-wizard-overlay';
        
        overlay.innerHTML = `
            <div class="setup-wizard">
                <div class="wizard-header">
                    <h2>🚀 Welcome to Windows AI</h2>
                    <p>Let's get you set up in just a few steps</p>
                    <div class="wizard-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" id="wizardProgressFill" style="width: 25%"></div>
                        </div>
                        <div class="progress-steps">
                            <span class="step-indicator active" data-step="1">1</span>
                            <span class="step-indicator" data-step="2">2</span>
                            <span class="step-indicator" data-step="3">3</span>
                            <span class="step-indicator" data-step="4">4</span>
                        </div>
                    </div>
                </div>

                <div class="wizard-content">
                    <!-- Step 1: Welcome -->
                    <div class="wizard-step active" data-step="1">
                        <div class="step-icon">👋</div>
                        <h3>Welcome!</h3>
                        <p>Windows AI is your intelligent assistant that brings the power of AI to your desktop.</p>
                        <div class="feature-list">
                            <div class="feature-item">
                                <span class="feature-icon">💬</span>
                                <span>Chat with AI using multiple providers</span>
                            </div>
                            <div class="feature-item">
                                <span class="feature-icon">🔌</span>
                                <span>Extend with powerful plugins</span>
                            </div>
                            <div class="feature-item">
                                <span class="feature-icon">⚡</span>
                                <span>Automate tasks and workflows</span>
                            </div>
                            <div class="feature-item">
                                <span class="feature-icon">🔒</span>
                                <span>Your data stays on your machine</span>
                            </div>
                        </div>
                    </div>

                    <!-- Step 2: Provider Detection -->
                    <div class="wizard-step" data-step="2">
                        <div class="step-icon">🧩</div>
                        <h3>Connect AI Providers and Local Runtimes</h3>
                        <p>Windows AI can detect installed CLIs and recommend local models for Ollama based on your hardware.</p>

                        <div class="wizard-note">
                            <span class="note-icon">ℹ️</span>
                            <span>Installed providers are shown as ready. Missing providers include install and authentication guidance.</span>
                        </div>

                        <div id="providerSetupStatus" class="wizard-inline-status">Detecting providers and hardware…</div>
                        <div id="providerDetectionList" class="feature-list"></div>

                        <div class="setup-summary" id="ollamaRecommendationSection" style="display:none;">
                            <h4>Recommended Ollama Models</h4>
                            <ul id="ollamaRecommendationList"></ul>
                        </div>
                    </div>

                    <!-- Step 3: API Keys -->
                    <div class="wizard-step" data-step="3">
                        <div class="step-icon">🔑</div>
                        <h3>Configure API Keys</h3>
                        <p>Add your AI provider API keys to enable AI features. You can skip this and add them later.</p>
                        
                        <div class="api-key-forms">
                            <div class="api-key-form">
                                <label>
                                    <span class="provider-name">OpenAI</span>
                                    <span class="provider-hint">(GPT-4, GPT-3.5)</span>
                                </label>
                                <input type="password" id="wizardOpenAIKey" placeholder="sk-..." class="wizard-input"/>
                                <a href="https://platform.openai.com/api-keys" target="_blank" class="get-key-link">Get API Key →</a>
                            </div>
                            
                            <div class="api-key-form">
                                <label>
                                    <span class="provider-name">Anthropic</span>
                                    <span class="provider-hint">(Claude)</span>
                                </label>
                                <input type="password" id="wizardAnthropicKey" placeholder="sk-ant-..." class="wizard-input"/>
                                <a href="https://console.anthropic.com/settings/keys" target="_blank" class="get-key-link">Get API Key →</a>
                            </div>
                            
                            <div class="api-key-form">
                                <label>
                                    <span class="provider-name">Google AI</span>
                                    <span class="provider-hint">(Gemini)</span>
                                </label>
                                <input type="password" id="wizardGoogleKey" placeholder="AIza..." class="wizard-input"/>
                                <a href="https://aistudio.google.com/app/apikey" target="_blank" class="get-key-link">Get API Key →</a>
                            </div>
                        </div>
                        
                        <div class="wizard-note">
                            <span class="note-icon">ℹ️</span>
                            <span>API keys are stored securely and never leave your device.</span>
                        </div>
                    </div>

                    <!-- Step 4: Model Selection & Complete -->
                    <div class="wizard-step" data-step="4">
                        <div class="step-icon">✅</div>
                        <h3>Pick Your Default Model and Finish</h3>
                        <p>Select the AI model you'd like to use by default. You can change this anytime.</p>
                        
                        <div class="model-selection-grid" id="wizardModelGrid">
                            <!-- Model options will be loaded dynamically -->
                        </div>

                        <div class="quick-tips">
                            <div class="tip-card">
                                <div class="tip-icon">💬</div>
                                <h4>Chat</h4>
                                <p>Start a conversation with AI in the Chat tab</p>
                            </div>
                            <div class="tip-card">
                                <div class="tip-icon">🔌</div>
                                <h4>Providers</h4>
                                <p>Use detected CLIs and local runtimes in one interface</p>
                            </div>
                            <div class="tip-card">
                                <div class="tip-icon">⚙️</div>
                                <h4>Settings</h4>
                                <p>Customize your experience in Settings</p>
                            </div>
                        </div>
                        
                        <div class="setup-summary" id="setupSummary">
                            <h4>Setup Summary</h4>
                            <ul id="setupSummaryList">
                                <li>Configuration saved</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <div class="wizard-footer">
                    <button id="wizardSkipBtn" class="wizard-btn secondary">Skip Setup</button>
                    <div class="wizard-nav">
                        <button id="wizardBackBtn" class="wizard-btn secondary" style="display: none;">Back</button>
                        <button id="wizardNextBtn" class="wizard-btn primary">Get Started</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);
        // Load dynamic data and attach event listeners
        this.loadProviderSetup();
        this.loadModelOptions();
        this.attachEventListeners();
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Navigation buttons
        document.getElementById('wizardNextBtn').addEventListener('click', () => this.nextStep());
        document.getElementById('wizardBackBtn').addEventListener('click', () => this.prevStep());
        document.getElementById('wizardSkipBtn').addEventListener('click', () => this.skipSetup());

        // Model selection - delegate to dynamic content
        document.getElementById('wizardModelGrid')?.addEventListener('click', (e) => {
            const option = e.target.closest('.model-option');
            if (!option) return;
            document.querySelectorAll('.model-option').forEach(o => o.classList.remove('selected'));
            option.classList.add('selected');
            this.setupData.selectedModel = option.dataset.model;
        });
    }

    async loadProviderSetup() {
        const statusEl = document.getElementById('providerSetupStatus');
        const listEl = document.getElementById('providerDetectionList');
        const ollamaSection = document.getElementById('ollamaRecommendationSection');
        const ollamaList = document.getElementById('ollamaRecommendationList');

        if (!statusEl || !listEl) return;

        statusEl.textContent = 'Detecting providers and hardware…';
        listEl.innerHTML = '';

        try {
            const response = await fetch(`${this.apiEndpoint}/integrations/providers/setup-plan`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            this.setupData.providerSetup = data;

            const providers = data.providers || [];
            const hardware = data.ollama?.hardware_profile || data.hardware || null;
            const recommendedModels = data.ollama?.recommended_models || [];

            statusEl.textContent = providers.length
                ? `Detected ${providers.filter(p => p.detected).length} installed provider(s)`
                : 'No provider data found';

            listEl.innerHTML = providers.map((provider) => this.renderProviderCard(provider)).join('');

            if (recommendedModels.length) {
                ollamaSection.style.display = 'block';
                const hardwareLabel = hardware
                    ? `${hardware.platform || 'Windows'} • ${hardware.cpu_count || '?'} CPU threads • ${hardware.total_memory_gb || '?'} GB RAM${hardware.gpu_hint ? ` • ${hardware.gpu_hint}` : ''}`
                    : 'Hardware profile unavailable';
                ollamaList.innerHTML = [
                    `<li><strong>Detected hardware:</strong> ${this.escapeHtml(hardwareLabel)}</li>`,
                    ...recommendedModels.map((model) => `<li><strong>${this.escapeHtml(model.id)}</strong> — ${this.escapeHtml(model.reason)}</li>`)
                ].join('');
            } else {
                ollamaSection.style.display = 'none';
            }
        } catch (error) {
            console.error('Failed to load provider setup plan:', error);
            statusEl.textContent = 'Provider detection unavailable right now';
            listEl.innerHTML = '<div class="empty-state">Detection failed. You can still configure providers later in Settings.</div>';
            if (ollamaSection) ollamaSection.style.display = 'none';
        }
    }

    renderProviderCard(provider) {
        const statusIcon = provider.recommended_action === 'ready'
            ? '✅'
            : provider.recommended_action === 'authenticate'
                ? '🔐'
                : '⬇️';
        const versionLine = provider.version ? `<div class="provider-hint-line">Version: ${this.escapeHtml(provider.version)}</div>` : '';
        const pathLine = provider.executable_path ? `<div class="provider-hint-line">Path: ${this.escapeHtml(provider.executable_path)}</div>` : '';
        const actionText = provider.recommended_action === 'ready'
            ? 'Ready to use in Windows AI'
            : provider.recommended_action === 'authenticate'
                ? 'Installed, but authentication is still needed'
                : 'Not detected. Use the install link to set it up';

        return `
            <div class="feature-item provider-detection-card ${this.escapeHtml(provider.recommended_action)}">
                <span class="feature-icon">${statusIcon}</span>
                <span>
                    <strong>${this.escapeHtml(provider.display_name || provider.provider_id)}</strong><br>
                    ${this.escapeHtml(actionText)}<br>
                    ${versionLine}
                    ${pathLine}
                    <span class="provider-hint-line">${this.escapeHtml(provider.auth_hint || '')}</span>
                    <a href="${this.escapeHtml(provider.install_url || '#')}" target="_blank" class="get-key-link">Install / Learn More →</a>
                </span>
            </div>
        `;
    }

    async loadModelOptions() {
        const grid = document.getElementById('wizardModelGrid');
        if (!grid) return;
        grid.innerHTML = '<div class="loading">Loading models...</div>';
        try {
            const res = await fetch(`${this.apiEndpoint}/models`);
            const json = await res.json();
            const models = json.models || json;
            grid.innerHTML = '';
            const providerIcons = {
                'OpenAI': '🤖',
                'Anthropic': '🧠',
                'Google': '✨',
                'Mistral': '🔥',
                'Ollama': '🦙',
                'Cohere': '🔡',
                'Together': '🔗',
                'Groq': '⚡',
                'system': '⚙️'
            };

            for (const m of models) {
                const el = document.createElement('div');
                el.className = 'model-option';
                el.dataset.model = m.id || m.model || m.name;
                const badge = m.preview ? 'preview' : (m.badge || '');
                const badgeHtml = badge ? `<div class="model-badge ${badge}">${badge.replace('-', ' ')}</div>` : '';
                const provider = m.provider || '';
                const title = m.name || m.model || m.id;
                const desc = m.description || '';
                const icon = providerIcons[provider] || '🤖';
                el.innerHTML = `${badgeHtml}<h4>${icon} ${title}</h4><p>${desc}</p><span class="model-provider-tag">${provider}</span>`;
                if (m.preview) {
                    el.title = 'Preview model - may be experimental and subject to change';
                } else if ((m.id || m.model) === 'auto') {
                    el.title = 'Automatic selection - the system will pick the best available model for your request';
                }
                grid.appendChild(el);
            }
        } catch (err) {
            console.error('Failed to load models:', err);
            grid.innerHTML = '<div class="empty-state">Failed to load models</div>';
        }
    }

    /**
     * Go to a specific step
     */
    goToStep(stepNumber) {
        this.currentStep = stepNumber;
        
        // Update step visibility
        document.querySelectorAll('.wizard-step').forEach(step => {
            step.classList.toggle('active', parseInt(step.dataset.step) === stepNumber);
        });

        // Update progress
        const progress = (stepNumber / this.totalSteps) * 100;
        document.getElementById('wizardProgressFill').style.width = `${progress}%`;
        
        // Update step indicators
        document.querySelectorAll('.step-indicator').forEach(indicator => {
            const step = parseInt(indicator.dataset.step);
            indicator.classList.toggle('active', step === stepNumber);
            indicator.classList.toggle('completed', step < stepNumber);
        });

        // Update buttons
        const backBtn = document.getElementById('wizardBackBtn');
        const nextBtn = document.getElementById('wizardNextBtn');
        const skipBtn = document.getElementById('wizardSkipBtn');

        backBtn.style.display = stepNumber > 1 ? 'block' : 'none';
        skipBtn.style.display = stepNumber < this.totalSteps ? 'block' : 'none';
        
        if (stepNumber === this.totalSteps) {
            nextBtn.textContent = 'Start Using Windows AI';
            this.generateSummary();
        } else if (stepNumber === 1) {
            nextBtn.textContent = 'Get Started';
        } else {
            nextBtn.textContent = 'Next';
        }
    }

    /**
     * Go to next step
     */
    async nextStep() {
        // Save data for current step
        await this.saveStepData();
        
        if (this.currentStep < this.totalSteps) {
            this.goToStep(this.currentStep + 1);
        } else {
            // Complete setup
            await this.completeSetup();
        }
    }

    /**
     * Go to previous step
     */
    prevStep() {
        if (this.currentStep > 1) {
            this.goToStep(this.currentStep - 1);
        }
    }

    /**
     * Save current step data
     */
    async saveStepData() {
        if (this.currentStep === 3) {
            // Collect API keys
            const openaiKey = document.getElementById('wizardOpenAIKey').value.trim();
            const anthropicKey = document.getElementById('wizardAnthropicKey').value.trim();
            const googleKey = document.getElementById('wizardGoogleKey').value.trim();

            if (openaiKey) this.setupData.apiKeys.openai = openaiKey;
            if (anthropicKey) this.setupData.apiKeys.anthropic = anthropicKey;
            if (googleKey) this.setupData.apiKeys.google = googleKey;

            // Save API keys to backend
            await this.saveApiKeys();
        }
    }

    /**
     * Save API keys to backend
     */
    async saveApiKeys() {
        for (const [provider, key] of Object.entries(this.setupData.apiKeys)) {
            try {
                await fetch(`${this.apiEndpoint}/api/credentials`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        provider: provider,
                        api_key: key
                    })
                });
            } catch (error) {
                console.error(`Failed to save ${provider} API key:`, error);
            }
        }
    }

    /**
     * Generate setup summary
     */
    async generateSummary() {
        const summaryList = document.getElementById('setupSummaryList');
        const items = [];

        const providerSetup = this.setupData.providerSetup;
        const readyProviders = providerSetup?.providers?.filter((item) => item.recommended_action === 'ready').length || 0;
        const missingProviders = providerSetup?.providers?.filter((item) => item.recommended_action === 'install').length || 0;
        if (providerSetup?.providers?.length) {
            items.push(`✓ ${readyProviders} provider(s) detected and ready`);
            if (missingProviders > 0) {
                items.push(`○ ${missingProviders} provider(s) can be installed later from the setup links`);
            }
        }

        const keyCount = Object.keys(this.setupData.apiKeys).length;
        if (keyCount > 0) {
            items.push(`✓ ${keyCount} API key(s) configured`);
        } else {
            items.push('○ No API keys configured (add in Settings)');
        }

        if (this.setupData.selectedModel) {
            let selectedName = this.setupData.selectedModel;
            // Try to read from the selected card's title in the grid
            const selectedEl = document.querySelector('.model-option.selected');
            if (selectedEl) {
                const titleEl = selectedEl.querySelector('h4');
                if (titleEl) selectedName = titleEl.textContent;
            } else {
                // As fallback, try to fetch model metadata from backend
                try {
                    const res = await fetch(`${this.apiEndpoint}/models/${this.setupData.selectedModel}`);
                    if (res.ok) {
                        const json = await res.json();
                        // Backend returns { status, model } in main endpoints
                        const modelObj = json.model || json;
                        selectedName = modelObj.name || modelObj.display_name || selectedName;
                    }
                } catch (err) {
                    console.warn('Failed to fetch model metadata', err);
                }
            }
            items.push(`✓ Default model: ${selectedName}`);
        } else {
            items.push('○ Using default model (GPT-3.5 Turbo)');
        }

        summaryList.innerHTML = items.map(item => `<li>${item}</li>`).join('');
    }

    /**
     * Complete the setup process
     */
    async completeSetup() {
        try {
            // Save selected model preference
            if (this.setupData.selectedModel) {
                await fetch(`${this.apiEndpoint}/api/settings`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        default_model: this.setupData.selectedModel
                    })
                });
            }

            // Mark setup as complete
            await fetch(`${this.apiEndpoint}/api/setup/complete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    completed: true,
                    timestamp: new Date().toISOString(),
                    provider_setup: this.setupData.providerSetup,
                })
            });

            // Hide wizard
            this.hide();
            
            // Trigger a refresh of the main UI
            if (typeof loadConversations === 'function') {
                loadConversations();
            }
            if (typeof loadAvailableModels === 'function') {
                loadAvailableModels();
            }

        } catch (error) {
            console.error('Failed to complete setup:', error);
            // Still hide wizard on error - user can configure in settings
            this.hide();
        }
    }

    /**
     * Skip setup entirely
     */
    async skipSetup() {
        try {
            // Mark setup as skipped
            await fetch(`${this.apiEndpoint}/api/setup/complete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    completed: true,
                    skipped: true,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (error) {
            console.error('Failed to skip setup:', error);
        }

        this.hide();
    }

    escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }
}

// Initialize setup wizard when DOM is ready
let setupWizard = null;

document.addEventListener('DOMContentLoaded', () => {
    setupWizard = new SetupWizard();
    
    // Check if this is first run after a short delay to let backend start
    setTimeout(() => {
        setupWizard.init().then(needed => {
            if (needed) {
                console.log('First-run setup wizard displayed');
            }
        });
    }, 1000);
});

// Export for use by other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SetupWizard };
}
