/**
 * Real-time Chat Interface
 * 
 * Integrates with WebSocket infrastructure for streaming chat responses
 */

class ChatInterface {
    constructor() {
        this.apiEndpoint = 'http://localhost:8010';
        this.wsEndpoint = 'ws://localhost:8010';
        this.chatSocket = null;
        this.currentConversationId = null;
        this.isStreaming = false;
        this.messageHistory = [];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.selectedModel = 'default';
        this.providerSetup = null;
        this.availableModels = [];
        
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        await this.loadModelSelectorOptions();
        await this.loadConversations();
        this.connectWebSocket();
    }
    
    setupEventListeners() {
        const sendBtn = this.getSendButton();
        const messageInput = this.getMessageInput();
        
        sendBtn?.addEventListener('click', () => this.sendMessage());
        messageInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        document.getElementById('newChatBtn')?.addEventListener('click', () => {
            this.createNewConversation();
        });
        
        this.getModelSelector()?.addEventListener('change', (e) => {
            this.selectedModel = e.target.value;
        });
        
        this.getStopStreamingButton()?.addEventListener('click', () => {
            this.stopStreaming();
        });
    }

    getSendButton() {
        return document.getElementById('sendMessageBtn') || document.getElementById('sendBtn');
    }

    getMessageInput() {
        return document.getElementById('messageInput') || document.getElementById('chatInput');
    }

    getModelSelector() {
        return document.getElementById('modelSelector') || document.getElementById('modelSelect');
    }

    getStopStreamingButton() {
        return document.getElementById('stopStreamingBtn');
    }

    isProviderExecutionTarget(model) {
        return typeof model === 'string' && (model.startsWith('cli:') || model.startsWith('ollama:'));
    }

    async loadModelSelectorOptions() {
        const selector = this.getModelSelector();
        if (!selector) return;

        try {
            const [models, providerSetup] = await Promise.all([
                this.fetchBackendModels(),
                this.fetchProviderSetup(),
            ]);

            this.availableModels = models;
            this.providerSetup = providerSetup;

            const currentValue = selector.value || this.selectedModel || 'default';
            selector.innerHTML = this.buildModelOptionsHtml(models, providerSetup);

            const optionValues = Array.from(selector.options).map((option) => option.value);
            this.selectedModel = optionValues.includes(currentValue) ? currentValue : (selector.options[0]?.value || 'default');
            selector.value = this.selectedModel;
        } catch (error) {
            console.error('Failed to load provider-aware model selector options:', error);
        }
    }

    async fetchBackendModels() {
        try {
            const response = await fetch(`${this.apiEndpoint}/models`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const json = await response.json();
            const models = json.models || json;
            return Array.isArray(models) ? models : [];
        } catch (error) {
            console.warn('Failed to fetch backend models for chat selector:', error);
            return [];
        }
    }

    async fetchProviderSetup() {
        try {
            if (window.winAI?.readConfig) {
                const config = await window.winAI.readConfig();
                if (config?.providerSetupPlan) {
                    return config.providerSetupPlan;
                }
            }
        } catch (error) {
            console.warn('Failed to read provider setup from local config:', error);
        }

        try {
            const response = await fetch(`${this.apiEndpoint}/integrations/providers/setup-plan`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.warn('Failed to fetch provider setup plan for chat selector:', error);
            return null;
        }
    }

    buildModelOptionsHtml(models, providerSetup) {
        const providerTargets = this.buildProviderTargets(providerSetup);
        const optionGroups = [];

        if (models.length) {
            optionGroups.push(`
                <optgroup label="Built-in Models">
                    ${models.map((model) => {
                        const value = this.escapeAttr(model.id || model.model || model.name || 'default');
                        const label = this.escapeHtml(model.name || model.model || model.id || 'Model');
                        const provider = this.escapeHtml(model.provider || 'Windows AI');
                        return `<option value="${value}">${label} — ${provider}</option>`;
                    }).join('')}
                </optgroup>
            `);
        }

        if (providerTargets.ready.length) {
            optionGroups.push(`
                <optgroup label="Detected CLI / Runtime Targets">
                    ${providerTargets.ready.map((target) => `<option value="${this.escapeAttr(target.value)}">${this.escapeHtml(target.label)}</option>`).join('')}
                </optgroup>
            `);
        }

        if (providerTargets.installable.length) {
            optionGroups.push(`
                <optgroup label="Install or Authenticate to Enable">
                    ${providerTargets.installable.map((target) => `<option value="${this.escapeAttr(target.value)}">${this.escapeHtml(target.label)}</option>`).join('')}
                </optgroup>
            `);
        }

        if (!optionGroups.length) {
            return '<option value="default">Default</option>';
        }

        return optionGroups.join('');
    }

    buildProviderTargets(providerSetup) {
        const ready = [];
        const installable = [];
        const providers = providerSetup?.providers || [];
        const ollamaModels = providerSetup?.ollama?.recommended_models || [];

        for (const provider of providers) {
            if (provider.provider_id === 'ollama' && provider.detected && ollamaModels.length) {
                for (const model of ollamaModels.slice(0, 3)) {
                    ready.push({
                        value: `ollama:${model.id}`,
                        label: `Ollama — ${model.id}`,
                    });
                }
                continue;
            }

            if (provider.recommended_action === 'ready') {
                ready.push({
                    value: `cli:${provider.provider_id}`,
                    label: `${provider.display_name || provider.provider_id} — Detected CLI`,
                });
            } else {
                installable.push({
                    value: `unavailable:${provider.provider_id}`,
                    label: `${provider.display_name || provider.provider_id} — ${provider.recommended_action}`,
                });
            }
        }

        return { ready, installable };
    }
    
    connectWebSocket() {
        if (this.chatSocket?.readyState === WebSocket.OPEN) {
            return;
        }
        
        const wsUrl = `${this.wsEndpoint}/api/ws/chat`;
        
        try {
            this.chatSocket = new WebSocket(wsUrl);
            
            this.chatSocket.onopen = () => {
                console.log('Chat WebSocket connected');
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected');
            };
            
            this.chatSocket.onmessage = (event) => {
                this.handleWebSocketMessage(JSON.parse(event.data));
            };
            
            this.chatSocket.onclose = () => {
                console.log('Chat WebSocket closed');
                this.updateConnectionStatus('disconnected');
                this.attemptReconnect();
            };
            
            this.chatSocket.onerror = (error) => {
                console.error('Chat WebSocket error:', error);
                this.updateConnectionStatus('error');
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus('error');
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnect attempts reached');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
        
        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
        setTimeout(() => this.connectWebSocket(), delay);
    }
    
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'chat_start':
                this.handleChatStart(message);
                break;
            case 'chat_chunk':
                this.handleChatChunk(message);
                break;
            case 'chat_complete':
                this.handleChatComplete(message);
                break;
            case 'chat_error':
                this.handleChatError(message);
                break;
            case 'pong':
                break;
            default:
                console.log('Unknown message type:', message.type);
        }
    }
    
    handleChatStart(message) {
        this.isStreaming = true;
        this.updateStreamingUI(true);
        
        this.appendMessage({
            role: 'assistant',
            content: '',
            id: message.message_id,
            streaming: true
        });
    }
    
    handleChatChunk(message) {
        const messageEl = document.querySelector(`[data-message-id="${message.message_id}"]`);
        if (messageEl) {
            const contentEl = messageEl.querySelector('.message-content');
            if (contentEl) {
                contentEl.textContent += message.chunk;
                this.scrollToBottom();
            }
        }
    }
    
    handleChatComplete(message) {
        this.isStreaming = false;
        this.updateStreamingUI(false);
        
        const messageEl = document.querySelector(`[data-message-id="${message.message_id}"]`);
        if (messageEl) {
            messageEl.classList.remove('streaming');
            const contentEl = messageEl.querySelector('.message-content');
            if (contentEl) {
                contentEl.innerHTML = this.formatMessage(message.content);
            }
        }
        
        this.messageHistory.push({
            role: 'assistant',
            content: message.content,
            timestamp: new Date().toISOString()
        });
    }
    
    handleChatError(message) {
        this.isStreaming = false;
        this.updateStreamingUI(false);
        
        this.appendMessage({
            role: 'error',
            content: `Error: ${message.error}`
        });
    }

    getProviderHistory(limit = 10) {
        return (this.messageHistory || [])
            .filter((message) => message && message.role && typeof message.content === 'string')
            .slice(-limit)
            .map((message) => ({
                role: message.role,
                content: message.content,
            }));
    }
    
    async sendMessage() {
        const input = this.getMessageInput();
        const content = input?.value.trim();
        
        if (!content || this.isStreaming) return;
        
        if (this.selectedModel?.startsWith('unavailable:')) {
            this.appendMessage({
                role: 'error',
                content: 'That provider is not ready yet. Open Settings or rerun setup to install or authenticate it first.'
            });
            return;
        }
        
        input.value = '';
        
        this.appendMessage({
            role: 'user',
            content: content
        });
        
        this.messageHistory.push({
            role: 'user',
            content: content,
            timestamp: new Date().toISOString()
        });

        if (this.isProviderExecutionTarget(this.selectedModel)) {
            await this.sendProviderTargetMessage(content);
            return;
        }
        
        if (this.chatSocket?.readyState === WebSocket.OPEN) {
            this.chatSocket.send(JSON.stringify({
                type: 'chat_message',
                conversation_id: this.currentConversationId,
                content: content,
                model: this.selectedModel || 'default'
            }));
        } else {
            await this.sendMessageREST(content);
        }
    }

    async sendProviderTargetMessage(content) {
        const messageId = `msg_${Date.now()}`;
        try {
            this.isStreaming = true;
            this.updateStreamingUI(true);

            this.appendMessage({
                role: 'assistant',
                content: '',
                id: messageId,
                streaming: true
            });

            const response = await fetch(`${this.apiEndpoint}/integrations/providers/chat/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    conversation_id: this.currentConversationId,
                    message: content,
                    model: this.selectedModel,
                    stream: true,
                    history: this.getProviderHistory(10),
                })
            });

            if (!response.ok || !response.body) {
                throw new Error(`Provider stream request failed (${response.status})`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let fullContent = '';
            let completed = false;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed) continue;
                    const event = JSON.parse(trimmed);
                    const messageEl = document.querySelector(`[data-message-id="${messageId}"]`);
                    const contentEl = messageEl?.querySelector('.message-content');

                    if (event.type === 'chunk') {
                        fullContent += event.content || '';
                        if (contentEl) {
                            contentEl.textContent = fullContent;
                            this.scrollToBottom();
                        }
                    } else if (event.type === 'complete') {
                        completed = true;
                        fullContent = event.content || fullContent;
                        if (messageEl) {
                            messageEl.classList.remove('streaming');
                        }
                        if (contentEl) {
                            contentEl.innerHTML = this.formatMessage(fullContent);
                        }
                    } else if (event.type === 'error') {
                        throw new Error(event.error || 'Provider streaming failed');
                    }
                }
            }

            if (!completed) {
                const fallbackPayload = await this.sendProviderTargetMessageFallback(content, messageId);
                fullContent = fallbackPayload;
            }

            this.messageHistory.push({
                role: 'assistant',
                content: fullContent,
                timestamp: new Date().toISOString(),
                model: this.selectedModel,
            });
        } catch (error) {
            console.error('Provider chat error:', error);
            try {
                const fallbackContent = await this.sendProviderTargetMessageFallback(content, messageId);
                this.messageHistory.push({
                    role: 'assistant',
                    content: fallbackContent,
                    timestamp: new Date().toISOString(),
                    model: this.selectedModel,
                });
            } catch (fallbackError) {
                console.error('Provider chat fallback failed:', fallbackError);
                this.appendMessage({
                    role: 'error',
                    content: `Failed to send provider request: ${fallbackError.message || error.message}`
                });
            }
        } finally {
            this.isStreaming = false;
            this.updateStreamingUI(false);
        }
    }

    async sendProviderTargetMessageFallback(content, messageId) {
        const response = await fetch(`${this.apiEndpoint}/integrations/providers/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                conversation_id: this.currentConversationId,
                message: content,
                model: this.selectedModel,
                stream: false,
                history: this.getProviderHistory(10),
            })
        });

        const payload = await response.json().catch(() => ({}));
        if (!response.ok || payload.status === 'error') {
            throw new Error(payload.error || payload.detail || 'Provider chat request failed');
        }

        const assistantContent = payload?.message?.content || payload?.provider_result?.content || '';
        const messageEl = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageEl) {
            messageEl.classList.remove('streaming');
            const contentEl = messageEl.querySelector('.message-content');
            if (contentEl) {
                contentEl.innerHTML = this.formatMessage(assistantContent);
            }
        }
        return assistantContent;
    }
    
    async sendMessageREST(content) {
        try {
            this.isStreaming = true;
            this.updateStreamingUI(true);
            
            const messageId = `msg_${Date.now()}`;
            this.appendMessage({
                role: 'assistant',
                content: '',
                id: messageId,
                streaming: true
            });
            
            const response = await fetch(`${this.apiEndpoint}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    conversation_id: this.currentConversationId,
                    content: content,
                    model: this.selectedModel || 'default',
                    stream: true
                })
            });
            
            if (!response.ok) throw new Error('Chat request failed');
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullContent = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                fullContent += chunk;
                
                const messageEl = document.querySelector(`[data-message-id="${messageId}"]`);
                if (messageEl) {
                    const contentEl = messageEl.querySelector('.message-content');
                    if (contentEl) {
                        contentEl.textContent = fullContent;
                        this.scrollToBottom();
                    }
                }
            }
            
            this.isStreaming = false;
            this.updateStreamingUI(false);
            
            const messageEl = document.querySelector(`[data-message-id="${messageId}"]`);
            if (messageEl) {
                messageEl.classList.remove('streaming');
                const contentEl = messageEl.querySelector('.message-content');
                if (contentEl) {
                    contentEl.innerHTML = this.formatMessage(fullContent);
                }
            }
            
        } catch (error) {
            console.error('Chat error:', error);
            this.isStreaming = false;
            this.updateStreamingUI(false);
            this.appendMessage({
                role: 'error',
                content: `Failed to send message: ${error.message}`
            });
        }
    }
    
    stopStreaming() {
        if (this.chatSocket?.readyState === WebSocket.OPEN) {
            this.chatSocket.send(JSON.stringify({
                type: 'stop_generation'
            }));
        }
        this.isStreaming = false;
        this.updateStreamingUI(false);
    }
    
    appendMessage({ role, content, id, streaming = false }) {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;
        
        const messageId = id || `msg_${Date.now()}`;
        const messageEl = document.createElement('div');
        messageEl.className = `message message-${role} ${streaming ? 'streaming' : ''}`;
        messageEl.dataset.messageId = messageId;
        
        const avatar = this.getAvatar(role);
        const formattedContent = streaming ? content : this.formatMessage(content);
        
        messageEl.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-body">
                <div class="message-header">
                    <span class="message-role">${this.getRoleName(role)}</span>
                    <span class="message-time">${new Date().toLocaleTimeString()}</span>
                </div>
                <div class="message-content">${formattedContent}</div>
                ${streaming ? '<div class="streaming-indicator"><span></span><span></span><span></span></div>' : ''}
            </div>
        `;
        
        messagesContainer.appendChild(messageEl);
        this.scrollToBottom();
    }
    
    getAvatar(role) {
        switch (role) {
            case 'user':
                return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>';
            case 'assistant':
                return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>';
            case 'error':
                return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';
            default:
                return '💬';
        }
    }
    
    getRoleName(role) {
        switch (role) {
            case 'user': return 'You';
            case 'assistant': return 'Windows AI';
            case 'error': return 'Error';
            default: return role;
        }
    }
    
    formatMessage(content) {
        if (!content) return '';
        
        let formatted = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        formatted = formatted.replace(
            /```(\w*)\n([\s\S]*?)```/g,
            '<pre><code class="language-$1">$2</code></pre>'
        );
        
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }
    
    scrollToBottom() {
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }
    
    updateStreamingUI(isStreaming) {
        const sendBtn = this.getSendButton();
        const stopBtn = this.getStopStreamingButton();
        const input = this.getMessageInput();
        
        if (sendBtn) sendBtn.disabled = isStreaming;
        if (stopBtn) stopBtn.style.display = isStreaming ? 'flex' : 'none';
        if (input) input.disabled = isStreaming;
    }
    
    updateConnectionStatus(status) {
        const indicator = document.getElementById('connectionIndicator');
        if (!indicator) return;
        
        indicator.className = `connection-indicator ${status}`;
        indicator.title = `Connection: ${status}`;
    }
    
    async loadConversations() {
        try {
            const response = await fetch(`${this.apiEndpoint}/api/conversations`);
            if (!response.ok) return;
            
            const conversations = await response.json();
            this.renderConversationList(conversations);
        } catch (error) {
            console.error('Failed to load conversations:', error);
        }
    }
    
    renderConversationList(conversations) {
        const listContainer = document.getElementById('conversationList');
        if (!listContainer) return;
        
        if (!conversations || conversations.length === 0) {
            listContainer.innerHTML = '<p class="no-conversations">No conversations yet</p>';
            return;
        }
        
        listContainer.innerHTML = conversations.map(conv => `
            <div class="conversation-item ${conv.id === this.currentConversationId ? 'active' : ''}" 
                 data-conversation-id="${conv.id}">
                <div class="conversation-title">${conv.title || 'New Conversation'}</div>
                <div class="conversation-date">${new Date(conv.created_at).toLocaleDateString()}</div>
            </div>
        `).join('');
        
        listContainer.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', () => {
                this.loadConversation(item.dataset.conversationId);
            });
        });
    }
    
    async loadConversation(conversationId) {
        try {
            const response = await fetch(`${this.apiEndpoint}/api/conversations/${conversationId}`);
            if (!response.ok) throw new Error('Failed to load conversation');
            
            const conversation = await response.json();
            this.currentConversationId = conversationId;
            this.messageHistory = conversation.messages || [];
            
            const messagesContainer = document.getElementById('chatMessages');
            if (messagesContainer) {
                messagesContainer.innerHTML = '';
                this.messageHistory.forEach(msg => {
                    this.appendMessage({
                        role: msg.role,
                        content: msg.content
                    });
                });
            }
            
            document.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.toggle('active', item.dataset.conversationId === conversationId);
            });
            
        } catch (error) {
            console.error('Failed to load conversation:', error);
        }
    }
    
    async createNewConversation() {
        try {
            const response = await fetch(`${this.apiEndpoint}/api/conversations`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: 'New Conversation'
                })
            });
            
            if (!response.ok) throw new Error('Failed to create conversation');
            
            const conversation = await response.json();
            this.currentConversationId = conversation.id;
            this.messageHistory = [];
            
            const messagesContainer = document.getElementById('chatMessages');
            if (messagesContainer) {
                messagesContainer.innerHTML = `
                    <div class="welcome-message">
                        <h2>👋 Start a new conversation</h2>
                        <p>Type your message below to get started.</p>
                    </div>
                `;
            }
            
            await this.loadConversations();
            
        } catch (error) {
            console.error('Failed to create conversation:', error);
        }
    }

    escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    escapeAttr(value) {
        return this.escapeHtml(value).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }
}

let chatInterface;
document.addEventListener('DOMContentLoaded', () => {
    chatInterface = new ChatInterface();
});
