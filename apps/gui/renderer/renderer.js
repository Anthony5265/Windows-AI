/**
 * Windows AI - Renderer Process
 * Main JavaScript for the Electron GUI
 */

// =====================================================================
// Configuration and State
// =====================================================================

const BACKEND_URL = 'http://127.0.0.1:8010';
let currentConversationId = null;
let isStreaming = false;

// =====================================================================
// Tab Switching
// =====================================================================

const tabs = document.querySelectorAll('.nav-btn');
const sections = document.querySelectorAll('.tab');

tabs.forEach(btn => {
  btn.addEventListener('click', () => {
    // Remove active class from all
    tabs.forEach(t => t.classList.remove('active'));
    sections.forEach(s => s.classList.remove('active'));

    // Add active class to clicked
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
  });
});

// =====================================================================
// Chat Functionality
// =====================================================================

const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const charCount = document.getElementById('charCount');
const modelSelect = document.getElementById('modelSelect');
const newChatBtn = document.getElementById('newChatBtn');
const conversationList = document.getElementById('conversationList');

// Auto-resize textarea
chatInput.addEventListener('input', () => {
  chatInput.style.height = 'auto';
  chatInput.style.height = chatInput.scrollHeight + 'px';

  // Update character count
  const length = chatInput.value.length;
  charCount.textContent = length;

  // Enable/disable send button
  sendBtn.disabled = length === 0;
});

// Send message on Enter (Shift+Enter for new line)
chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Send button click
sendBtn.addEventListener('click', sendMessage);

// Quick action buttons
document.querySelectorAll('.quick-action').forEach(btn => {
  btn.addEventListener('click', () => {
    const prompt = btn.dataset.prompt;
    chatInput.value = prompt;
    chatInput.dispatchEvent(new Event('input'));
    sendMessage();
  });
});

// New chat button
newChatBtn.addEventListener('click', () => {
  currentConversationId = null;
  clearChatMessages();
  showWelcomeMessage();
  updateStatus('Ready for new conversation');
});

/**
 * Send a chat message
 */
async function sendMessage() {
  const message = chatInput.value.trim();
  if (!message || isStreaming) return;

  // Clear welcome message if present
  const welcomeMsg = chatMessages.querySelector('.welcome-message');
  if (welcomeMsg) {
    welcomeMsg.remove();
  }

  // Add user message to UI
  addMessage('user', message);

  // Clear input
  chatInput.value = '';
  chatInput.style.height = 'auto';
  charCount.textContent = '0';
  sendBtn.disabled = true;

  // Show typing indicator
  const typingIndicator = showTypingIndicator();

  // Send to backend
  try {
    isStreaming = true;
    updateStatus('AI is thinking...');

    const response = await fetch(`${BACKEND_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: message,
        conversation_id: currentConversationId,
        model: modelSelect.value,
        stream: true,
        temperature: 0.7
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Remove typing indicator
    typingIndicator.remove();

    // Process streaming response
    const assistantMessageEl = createMessageElement('assistant', '');
    chatMessages.appendChild(assistantMessageEl);
    scrollToBottom();

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullResponse = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));

          if (data.chunk) {
            fullResponse += data.chunk;
            updateMessageContent(assistantMessageEl, fullResponse);
            scrollToBottom();
          }

          if (data.done) {
            currentConversationId = data.conversation_id;
            loadConversations();
          }
        }
      }
    }

    updateStatus('Ready');
    isStreaming = false;

  } catch (error) {
    console.error('Error sending message:', error);
    typingIndicator.remove();
    addMessage('assistant', `Error: ${error.message}. Please make sure the backend is running at ${BACKEND_URL}`);
    updateStatus('Error - Backend not responding');
    isStreaming = false;
  }
}

/**
 * Create a message element
 */
function createMessageElement(role, content) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.textContent = role === 'user' ? 'U' : 'AI';

  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  contentDiv.textContent = content;

  const timestamp = document.createElement('div');
  timestamp.className = 'message-timestamp';
  timestamp.textContent = new Date().toLocaleTimeString();

  messageDiv.appendChild(avatar);
  contentDiv.appendChild(timestamp);
  messageDiv.appendChild(contentDiv);

  return messageDiv;
}

/**
 * Add a message to the chat
 */
function addMessage(role, content) {
  const messageEl = createMessageElement(role, content);
  chatMessages.appendChild(messageEl);
  scrollToBottom();
}

/**
 * Update message content (for streaming)
 */
function updateMessageContent(messageEl, content) {
  const contentDiv = messageEl.querySelector('.message-content');
  const timestamp = contentDiv.querySelector('.message-timestamp');
  contentDiv.textContent = content;
  contentDiv.appendChild(timestamp);
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
  const indicator = document.createElement('div');
  indicator.className = 'message assistant';
  indicator.innerHTML = `
    <div class="message-avatar">AI</div>
    <div class="message-content">
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `;
  chatMessages.appendChild(indicator);
  scrollToBottom();
  return indicator;
}

/**
 * Show welcome message
 */
function showWelcomeMessage() {
  const welcomeDiv = document.createElement('div');
  welcomeDiv.className = 'welcome-message';
  welcomeDiv.innerHTML = `
    <h2>👋 Welcome to Windows AI</h2>
    <p>Your intelligent assistant for everything Windows</p>
    <div class="quick-actions">
      <button class="quick-action" data-prompt="Help me organize my files">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
        Organize Files
      </button>
      <button class="quick-action" data-prompt="What system information can you show me?">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"/>
          <line x1="7" y1="2" x2="7" y2="22"/>
          <line x1="17" y1="2" x2="17" y2="22"/>
          <line x1="2" y1="12" x2="22" y2="12"/>
          <line x1="2" y1="7" x2="7" y2="7"/>
          <line x1="2" y1="17" x2="7" y2="17"/>
          <line x1="17" y1="17" x2="22" y2="17"/>
          <line x1="17" y1="7" x2="22" y2="7"/>
        </svg>
        System Info
      </button>
      <button class="quick-action" data-prompt="Help me automate a task">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
          <circle cx="12" cy="12" r="3"/>
        </svg>
        Automation
      </button>
      <button class="quick-action" data-prompt="What can you help me with?">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        Learn More
      </button>
    </div>
  `;

  chatMessages.appendChild(welcomeDiv);

  // Re-attach event listeners to new quick action buttons
  welcomeDiv.querySelectorAll('.quick-action').forEach(btn => {
    btn.addEventListener('click', () => {
      const prompt = btn.dataset.prompt;
      chatInput.value = prompt;
      chatInput.dispatchEvent(new Event('input'));
      sendMessage();
    });
  });
}

/**
 * Clear chat messages
 */
function clearChatMessages() {
  chatMessages.innerHTML = '';
}

/**
 * Scroll chat to bottom
 */
function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Load conversations from backend
 */
async function loadConversations() {
  try {
    const response = await fetch(`${BACKEND_URL}/conversations`);
    if (!response.ok) return;

    const data = await response.json();
    displayConversations(data.conversations);
  } catch (error) {
    console.error('Error loading conversations:', error);
  }
}

/**
 * Display conversations in sidebar
 */
function displayConversations(conversations) {
  conversationList.innerHTML = '';

  Object.keys(conversations).reverse().forEach(convId => {
    const messages = conversations[convId];
    if (messages.length === 0) return;

    const firstMessage = messages[0];
    const preview = firstMessage.content.slice(0, 50) + (firstMessage.content.length > 50 ? '...' : '');

    const btn = document.createElement('button');
    btn.className = 'conversation-item';
    if (convId === currentConversationId) {
      btn.classList.add('active');
    }
    btn.textContent = preview;
    btn.onclick = () => loadConversation(convId);

    conversationList.appendChild(btn);
  });
}

/**
 * Load a specific conversation
 */
async function loadConversation(convId) {
  try {
    const response = await fetch(`${BACKEND_URL}/conversations/${convId}`);
    if (!response.ok) return;

    const data = await response.json();
    currentConversationId = convId;

    clearChatMessages();

    data.messages.forEach(msg => {
      addMessage(msg.role, msg.content);
    });

    // Update sidebar
    document.querySelectorAll('.conversation-item').forEach(item => {
      item.classList.remove('active');
    });
    event.target.classList.add('active');

    updateStatus(`Loaded conversation ${convId}`);
  } catch (error) {
    console.error('Error loading conversation:', error);
  }
}

// =====================================================================
// Workflows
// =====================================================================

document.getElementById('runEcho').addEventListener('click', async () => {
  const output = document.getElementById('wfOut');
  output.textContent = 'Running workflow...';

  try {
    const res = await fetch('http://127.0.0.1:15777/workflows/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'echo', inputs: {} })
    });
    const data = await res.json();
    output.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    output.textContent = `Error: ${error.message}`;
  }
});

// =====================================================================
// Settings
// =====================================================================

const themeSelect = document.getElementById('theme');
const temperatureInput = document.getElementById('temperature');
const tempValue = document.getElementById('tempValue');

// Temperature slider
temperatureInput.addEventListener('input', () => {
  tempValue.textContent = temperatureInput.value;
});

// Save settings
document.getElementById('saveCfg').addEventListener('click', async () => {
  const config = {
    ui: {
      theme: themeSelect.value
    },
    network: {
      bind: document.getElementById('bind').value,
      port: document.getElementById('port').value
    },
    model: {
      default: document.getElementById('defaultModel').value,
      temperature: parseFloat(temperatureInput.value)
    }
  };

  try {
    await window.winAI.writeConfig(config);
    alert('Settings saved successfully!');
    applyTheme(config.ui.theme);
  } catch (error) {
    alert('Error saving settings: ' + error.message);
  }
});

// Reset settings
document.getElementById('resetCfg').addEventListener('click', () => {
  if (confirm('Reset all settings to defaults?')) {
    themeSelect.value = 'system';
    document.getElementById('bind').value = '127.0.0.1';
    document.getElementById('port').value = '8010';
    document.getElementById('defaultModel').value = 'gpt-3.5-turbo';
    temperatureInput.value = '0.7';
    tempValue.textContent = '0.7';
    applyTheme('system');
  }
});

/**
 * Apply theme
 */
function applyTheme(theme) {
  if (theme === 'dark') {
    document.body.setAttribute('data-theme', 'dark');
  } else if (theme === 'light') {
    document.body.removeAttribute('data-theme');
  } else {
    // System theme - detect from OS
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (isDark) {
      document.body.setAttribute('data-theme', 'dark');
    } else {
      document.body.removeAttribute('data-theme');
    }
  }
}

// =====================================================================
// Status Updates
// =====================================================================

function updateStatus(message) {
  const statusEl = document.getElementById('status');
  statusEl.textContent = `●  ${message}`;
}

// =====================================================================
// Initialization
// =====================================================================

(async () => {
  try {
    // Display environment info
    const env = await window.winAI.envInfo();
    document.getElementById('env').textContent =
      `${env.platform}/${env.arch} • Electron ${env.versions.electron} • Node ${env.versions.node}`;

    // Load config
    const cfg = await window.winAI.readConfig();
    if (cfg) {
      if (cfg.network?.bind) document.getElementById('bind').value = cfg.network.bind;
      if (cfg.network?.port) document.getElementById('port').value = cfg.network.port;
      if (cfg.ui?.theme) {
        themeSelect.value = cfg.ui.theme;
        applyTheme(cfg.ui.theme);
      }
      if (cfg.model?.default) document.getElementById('defaultModel').value = cfg.model.default;
      if (cfg.model?.temperature) {
        temperatureInput.value = cfg.model.temperature;
        tempValue.textContent = cfg.model.temperature;
      }
    }

    // Check backend connectivity
    try {
      const response = await fetch(`${BACKEND_URL}/health`, { timeout: 2000 });
      if (response.ok) {
        updateStatus('Connected to backend');
        loadConversations();
      } else {
        updateStatus('Backend unreachable');
      }
    } catch (error) {
      updateStatus('Backend offline - Please start the backend service');
      console.warn('Backend not available:', error);
    }

  } catch (error) {
    console.error('Initialization error:', error);
    updateStatus('Initialization error');
  }
})();

// Listen for system theme changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
  if (themeSelect.value === 'system') {
    applyTheme('system');
  }
});

console.log('Windows AI Renderer initialized');
