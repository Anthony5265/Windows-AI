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
        
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        await this.loadConversations();
        this.connectWebSocket();
    }
    
    setupEventListeners() {
        // Send message
        const sendBtn = document.getElementById('sendMessageBtn');
        const messageInput = document.getElementById('messageInput');
        
        sendBtn?.addEventListener('click', () => this.sendMessage());
        messageInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // New conversation
        document.getElementById('newChatBtn')?.addEventListener('click', () => {
            this.createNewConversation();
        });
        
        // Model selector
        document.getElementById('modelSelector')?.addEventListener('change', (e) => {
            this.selectedModel = e.target.value;
        });
        
        // Stop streaming
        document.getElementById('stopStreamingBtn')?.addEventListener('click', () => {
            this.stopStreaming();
        });
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
                // Heartbeat response
                break;
            default:
                console.log('Unknown message type:', message.type);
        }
    }
    
    handleChatStart(message) {
        this.isStreaming = true;
        this.updateStreamingUI(true);
        
        // Create assistant message container
        this.appendMessage({
            role: 'assistant',
            content: '',
            id: message.message_id,
            streaming: true
        });
    }
    
    handleChatChunk(message) {
        // Append chunk to current streaming message
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
        
        // Update message to final state
        const messageEl = document.querySelector(`[data-message-id="${message.message_id}"]`);
        if (messageEl) {
            messageEl.classList.remove('streaming');
            const contentEl = messageEl.querySelector('.message-content');
            if (contentEl) {
                contentEl.innerHTML = this.formatMessage(message.content);
            }
        }
        
        // Save to history
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
    
    async sendMessage() {
        const input = document.getElementById('messageInput');
        const content = input?.value.trim();
        
        if (!content || this.isStreaming) return;
        
        // Clear input
        input.value = '';
        
        // Add user message to UI
        this.appendMessage({
            role: 'user',
            content: content
        });
        
        // Save to history
        this.messageHistory.push({
            role: 'user',
            content: content,
            timestamp: new Date().toISOString()
        });
        
        // Send via WebSocket or REST API
        if (this.chatSocket?.readyState === WebSocket.OPEN) {
            this.chatSocket.send(JSON.stringify({
                type: 'chat_message',
                conversation_id: this.currentConversationId,
                content: content,
                model: this.selectedModel || 'default'
            }));
        } else {
            // Fallback to REST API with SSE
            await this.sendMessageREST(content);
        }
    }
    
    async sendMessageREST(content) {
        try {
            this.isStreaming = true;
            this.updateStreamingUI(true);
            
            // Create assistant message container
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
            
            // Read streaming response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullContent = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                fullContent += chunk;
                
                // Update UI
                const messageEl = document.querySelector(`[data-message-id="${messageId}"]`);
                if (messageEl) {
                    const contentEl = messageEl.querySelector('.message-content');
                    if (contentEl) {
                        contentEl.textContent = fullContent;
                        this.scrollToBottom();
                    }
                }
            }
            
            // Finalize
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
        
        // Escape HTML
        let formatted = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // Code blocks
        formatted = formatted.replace(
            /```(\w*)\n([\s\S]*?)```/g,
            '<pre><code class="language-$1">$2</code></pre>'
        );
        
        // Inline code
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Bold
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Italic
        formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // Line breaks
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
        const sendBtn = document.getElementById('sendMessageBtn');
        const stopBtn = document.getElementById('stopStreamingBtn');
        const input = document.getElementById('messageInput');
        
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
        
        // Add click handlers
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
            
            // Clear and render messages
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
            
            // Update conversation list selection
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
            
            // Clear messages
            const messagesContainer = document.getElementById('chatMessages');
            if (messagesContainer) {
                messagesContainer.innerHTML = `
                    <div class="welcome-message">
                        <h2>👋 Start a new conversation</h2>
                        <p>Type your message below to get started.</p>
                    </div>
                `;
            }
            
            // Reload conversation list
            await this.loadConversations();
            
        } catch (error) {
            console.error('Failed to create conversation:', error);
        }
    }
}

// Initialize chat interface when DOM is ready
let chatInterface;
document.addEventListener('DOMContentLoaded', () => {
    chatInterface = new ChatInterface();
});
