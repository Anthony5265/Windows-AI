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

// Note: Save settings handler is defined later with backend integration

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

// Note: Initialization moved to enhanced initialization section below

// Listen for system theme changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
  if (themeSelect.value === 'system') {
    applyTheme('system');
  }
});

// =====================================================================
// Automation - Folder Watchers & Scheduled Tasks
// =====================================================================

const addWatcherBtn = document.getElementById('addWatcherBtn');
const addTaskBtn = document.getElementById('addTaskBtn');
const watcherModal = document.getElementById('watcherModal');
const taskModal = document.getElementById('taskModal');
const saveWatcherBtn = document.getElementById('saveWatcherBtn');
const saveTaskBtn = document.getElementById('saveTaskBtn');

// Load watchers from backend
async function loadWatchers() {
  try {
    const response = await fetch(`${BACKEND_URL}/automation/watchers`);
    const data = await response.json();
    const watchersList = document.getElementById('watchersList');

    if (data.watchers && data.watchers.length > 0) {
      watchersList.innerHTML = data.watchers.map(watcher => `
        <div class="automation-card" data-id="${watcher.id}">
          <div class="automation-card-content">
            <div class="automation-card-title">
              📁 ${watcher.name}
              <span class="status-badge ${watcher.running ? 'active' : 'inactive'}">
                ${watcher.running ? '● Active' : '○ Inactive'}
              </span>
            </div>
            <div class="automation-card-description">${watcher.path}</div>
            <div class="automation-card-meta">
              <span>Patterns: ${watcher.patterns.join(', ')}</span>
              <span>Events: ${watcher.events.join(', ')}</span>
              <span>Action: ${watcher.action}</span>
            </div>
          </div>
          <div class="automation-card-actions">
            <button class="icon-btn" onclick="toggleWatcher('${watcher.id}', ${watcher.running})">
              ${watcher.running ? '⏸' : '▶'}
            </button>
            <button class="icon-btn danger" onclick="deleteWatcher('${watcher.id}')">🗑</button>
          </div>
        </div>
      `).join('');
    } else {
      watchersList.innerHTML = `
        <div class="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
          </svg>
          <p>No folder watchers configured</p>
          <p class="hint">Click "Add Watcher" to monitor folders for file changes</p>
        </div>
      `;
    }
  } catch (error) {
    console.error('Error loading watchers:', error);
  }
}

// Load tasks from backend
async function loadTasks() {
  try {
    const response = await fetch(`${BACKEND_URL}/automation/tasks`);
    const data = await response.json();
    const tasksList = document.getElementById('tasksList');

    if (data.tasks && data.tasks.length > 0) {
      tasksList.innerHTML = data.tasks.map(task => {
        const nextRun = task.next_run ? new Date(task.next_run).toLocaleString() : 'N/A';
        return `
          <div class="automation-card" data-id="${task.id}">
            <div class="automation-card-content">
              <div class="automation-card-title">
                ⏰ ${task.name}
                <span class="status-badge ${task.enabled ? 'active' : 'inactive'}">
                  ${task.enabled ? '● Enabled' : '○ Disabled'}
                </span>
              </div>
              <div class="automation-card-description">${task.description}</div>
              <div class="automation-card-meta">
                <span>Schedule: ${task.schedule}</span>
                <span>Next run: ${nextRun}</span>
                <span>Runs: ${task.run_count}</span>
              </div>
            </div>
            <div class="automation-card-actions">
              <button class="icon-btn" onclick="toggleTask('${task.id}', ${task.enabled})">
                ${task.enabled ? '⏸' : '▶'}
              </button>
              <button class="icon-btn danger" onclick="deleteTask('${task.id}')">🗑</button>
            </div>
          </div>
        `;
      }).join('');
    } else {
      tasksList.innerHTML = `
        <div class="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v6l4 2"/>
          </svg>
          <p>No scheduled tasks configured</p>
          <p class="hint">Click "Add Task" to schedule AI tasks to run automatically</p>
        </div>
      `;
    }
  } catch (error) {
    console.error('Error loading tasks:', error);
  }
}

// Toggle watcher on/off
window.toggleWatcher = async function(watcherId, isRunning) {
  try {
    const endpoint = isRunning ? 'stop' : 'start';
    const response = await fetch(`${BACKEND_URL}/automation/watchers/${watcherId}/${endpoint}`, {
      method: 'POST'
    });
    if (response.ok) {
      await loadWatchers();
      updateStatus(`Watcher ${isRunning ? 'stopped' : 'started'}`);
    }
  } catch (error) {
    console.error('Error toggling watcher:', error);
    updateStatus('Error toggling watcher');
  }
};

// Delete watcher
window.deleteWatcher = async function(watcherId) {
  if (!confirm('Are you sure you want to delete this watcher?')) return;
  try {
    const response = await fetch(`${BACKEND_URL}/automation/watchers/${watcherId}`, {
      method: 'DELETE'
    });
    if (response.ok) {
      await loadWatchers();
      updateStatus('Watcher deleted');
    }
  } catch (error) {
    console.error('Error deleting watcher:', error);
    updateStatus('Error deleting watcher');
  }
};

// Toggle task on/off
window.toggleTask = async function(taskId, isEnabled) {
  try {
    const response = await fetch(`${BACKEND_URL}/automation/tasks/${taskId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: !isEnabled })
    });
    if (response.ok) {
      await loadTasks();
      updateStatus(`Task ${isEnabled ? 'disabled' : 'enabled'}`);
    }
  } catch (error) {
    console.error('Error toggling task:', error);
    updateStatus('Error toggling task');
  }
};

// Delete task
window.deleteTask = async function(taskId) {
  if (!confirm('Are you sure you want to delete this task?')) return;
  try {
    const response = await fetch(`${BACKEND_URL}/automation/tasks/${taskId}`, {
      method: 'DELETE'
    });
    if (response.ok) {
      await loadTasks();
      updateStatus('Task deleted');
    }
  } catch (error) {
    console.error('Error deleting task:', error);
    updateStatus('Error deleting task');
  }
};

// Open watcher modal
addWatcherBtn?.addEventListener('click', () => {
  watcherModal.classList.remove('hidden');
});

// Save watcher
saveWatcherBtn?.addEventListener('click', async () => {
  const watcher = {
    id: `watcher-${Date.now()}`,
    name: document.getElementById('watcherName').value,
    path: document.getElementById('watcherPath').value,
    patterns: document.getElementById('watcherPatterns').value.split(',').map(p => p.trim()),
    events: [
      document.getElementById('watchCreated').checked ? 'created' : null,
      document.getElementById('watchModified').checked ? 'modified' : null,
      document.getElementById('watchDeleted').checked ? 'deleted' : null
    ].filter(Boolean),
    action: document.getElementById('watcherAction').value,
    custom_prompt: document.getElementById('watcherPrompt').value || null,
    enabled: true,
    recursive: true
  };

  try {
    const response = await fetch(`${BACKEND_URL}/automation/watchers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(watcher)
    });
    if (response.ok) {
      watcherModal.classList.add('hidden');
      await loadWatchers();
      updateStatus('Watcher created successfully');
      // Clear form
      document.getElementById('watcherName').value = '';
      document.getElementById('watcherPath').value = '';
      document.getElementById('watcherPatterns').value = '';
      document.getElementById('watcherPrompt').value = '';
    }
  } catch (error) {
    console.error('Error creating watcher:', error);
    updateStatus('Error creating watcher');
  }
});

// Open task modal
addTaskBtn?.addEventListener('click', () => {
  taskModal.classList.remove('hidden');
});

// Save task
saveTaskBtn?.addEventListener('click', async () => {
  const task = {
    id: `task-${Date.now()}`,
    name: document.getElementById('taskName').value,
    description: document.getElementById('taskDescription').value,
    schedule_type: document.getElementById('taskScheduleType').value,
    schedule: document.getElementById('taskSchedule').value,
    action: document.getElementById('taskAction').value,
    prompt: document.getElementById('taskPrompt').value,
    enabled: true
  };

  try {
    const response = await fetch(`${BACKEND_URL}/automation/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(task)
    });
    if (response.ok) {
      taskModal.classList.add('hidden');
      await loadTasks();
      updateStatus('Task created successfully');
      // Clear form
      document.getElementById('taskName').value = '';
      document.getElementById('taskDescription').value = '';
      document.getElementById('taskSchedule').value = '';
      document.getElementById('taskPrompt').value = '';
    } else {
      const error = await response.json();
      updateStatus(`Error: ${error.detail}`);
    }
  } catch (error) {
    console.error('Error creating task:', error);
    updateStatus('Error creating task');
  }
});

// Load automation data when tab is opened
document.querySelector('[data-tab="automation"]')?.addEventListener('click', () => {
  loadWatchers();
  loadTasks();
});

// =====================================================================
// Plugin Marketplace
// =====================================================================

let allPlugins = [];
let currentPluginFilter = 'all';

// Load plugins from backend
async function loadPlugins() {
  try {
    const response = await fetch(`${BACKEND_URL}/plugins`);
    if (!response.ok) {
      throw new Error('Failed to load plugins');
    }

    const data = await response.json();
    allPlugins = data.plugins || [];

    // Update stats
    document.getElementById('pluginsCount').textContent = `${allPlugins.length} plugins`;
    const activeCount = allPlugins.filter(p => p.enabled).length;
    document.getElementById('pluginsActive').textContent = `${activeCount} active`;

    displayPlugins();
  } catch (error) {
    console.error('Error loading plugins:', error);
    document.getElementById('pluginsList').innerHTML = `
      <div class="empty-state">
        <p>Failed to load plugins</p>
        <p class="hint">Make sure the backend is running at ${BACKEND_URL}</p>
      </div>
    `;
  }
}

// Display plugins in grid
function displayPlugins() {
  const pluginsList = document.getElementById('pluginsList');

  // Filter plugins
  let filtered = allPlugins;
  if (currentPluginFilter !== 'all') {
    filtered = allPlugins.filter(p => p.type === currentPluginFilter);
  }

  if (filtered.length === 0) {
    pluginsList.innerHTML = `
      <div class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6"/>
        </svg>
        <p>No plugins found</p>
        <p class="hint">Try a different filter or check back later</p>
      </div>
    `;
    return;
  }

  pluginsList.innerHTML = filtered.map(plugin => `
    <div class="plugin-card ${plugin.enabled ? 'enabled' : 'disabled'}">
      <div class="plugin-card-header">
        <div class="plugin-icon">${getPluginIcon(plugin.type)}</div>
        <div class="plugin-info">
          <h3 class="plugin-name">${plugin.name || plugin.id}</h3>
          <span class="plugin-type">${plugin.type}</span>
        </div>
        <div class="plugin-toggle">
          <label class="toggle-switch">
            <input type="checkbox" ${plugin.enabled ? 'checked' : ''}
                   onchange="togglePlugin('${plugin.id}', this.checked)">
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>
      <p class="plugin-description">${plugin.description || 'No description available'}</p>
      <div class="plugin-meta">
        <span>v${plugin.version || '1.0.0'}</span>
        <span>${plugin.author || 'Unknown'}</span>
      </div>
      <div class="plugin-actions">
        <button class="btn-secondary" onclick="showPluginDetails('${plugin.id}')">Details</button>
        ${plugin.enabled && plugin.actions ?
          `<button class="btn-primary" onclick="executePlugin('${plugin.id}')">Execute</button>` :
          ''
        }
      </div>
    </div>
  `).join('');
}

// Get icon for plugin type
function getPluginIcon(type) {
  const icons = {
    'action': '⚡',
    'tool': '🔧',
    'integration': '🔗',
    'automation': '🤖',
    'ui': '🎨'
  };
  return icons[type] || '🔌';
}

// Toggle plugin enabled/disabled
window.togglePlugin = async function(pluginId, enabled) {
  try {
    const endpoint = enabled ? 'enable' : 'disable';
    const response = await fetch(`${BACKEND_URL}/plugins/${pluginId}/${endpoint}`, {
      method: 'POST'
    });

    if (response.ok) {
      // Update local state
      const plugin = allPlugins.find(p => p.id === pluginId);
      if (plugin) {
        plugin.enabled = enabled;
      }

      // Reload plugins
      await loadPlugins();
      updateStatus(`Plugin ${enabled ? 'enabled' : 'disabled'}`);
    } else {
      throw new Error('Failed to toggle plugin');
    }
  } catch (error) {
    console.error('Error toggling plugin:', error);
    updateStatus('Error toggling plugin');
    // Revert checkbox
    await loadPlugins();
  }
};

// Show plugin details in modal
window.showPluginDetails = async function(pluginId) {
  try {
    const response = await fetch(`${BACKEND_URL}/plugins/${pluginId}`);
    const plugin = await response.json();

    const modal = document.getElementById('pluginModal');
    document.getElementById('pluginModalTitle').textContent = plugin.name || plugin.id;

    const actions = plugin.schema?.actions || [];
    const actionsList = actions.length > 0
      ? `<h4>Available Actions</h4><ul>${actions.map(a => `<li><strong>${a.name}</strong>: ${a.description || 'No description'}</li>`).join('')}</ul>`
      : '<p>No actions available</p>';

    document.getElementById('pluginModalBody').innerHTML = `
      <p><strong>ID:</strong> ${plugin.id}</p>
      <p><strong>Type:</strong> ${plugin.type}</p>
      <p><strong>Version:</strong> ${plugin.version || '1.0.0'}</p>
      <p><strong>Author:</strong> ${plugin.author || 'Unknown'}</p>
      <p><strong>Description:</strong> ${plugin.description || 'No description'}</p>
      ${actionsList}
      <p><strong>Enabled:</strong> ${plugin.enabled ? 'Yes' : 'No'}</p>
      <p><strong>Initialized:</strong> ${plugin.initialized ? 'Yes' : 'No'}</p>
    `;

    const actionBtn = document.getElementById('pluginModalAction');
    actionBtn.textContent = plugin.enabled ? 'Disable' : 'Enable';
    actionBtn.onclick = async () => {
      await togglePlugin(pluginId, !plugin.enabled);
      modal.classList.add('hidden');
    };

    modal.classList.remove('hidden');
  } catch (error) {
    console.error('Error loading plugin details:', error);
    updateStatus('Error loading plugin details');
  }
};

// Execute plugin (simplified - prompts for action)
window.executePlugin = async function(pluginId) {
  try {
    const response = await fetch(`${BACKEND_URL}/plugins/${pluginId}`);
    const plugin = await response.json();

    const actions = plugin.schema?.actions || [];
    if (actions.length === 0) {
      alert('This plugin has no executable actions');
      return;
    }

    // For now, execute the first action with empty params
    // In production, show action selector modal
    const action = actions[0].name;

    const execResponse = await fetch(`${BACKEND_URL}/plugins/${pluginId}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: action, parameters: {} })
    });

    const result = await execResponse.json();
    alert(`Plugin executed:\n${JSON.stringify(result, null, 2)}`);
    updateStatus('Plugin executed successfully');
  } catch (error) {
    console.error('Error executing plugin:', error);
    alert('Error executing plugin: ' + error.message);
  }
};

// Plugin filter
document.getElementById('pluginTypeFilter')?.addEventListener('change', (e) => {
  currentPluginFilter = e.target.value;
  displayPlugins();
});

// Load plugins when tab is opened
document.querySelector('[data-tab="plugins"]')?.addEventListener('click', () => {
  loadPlugins();
});

// =====================================================================
// Model Management UI
// =====================================================================

let allModels = [];
let installedModels = [];
let currentModelFilter = 'all';
let currentDownload = null;
let downloadCheckInterval = null;

// Load available models
async function loadAvailableModelsData() {
  try {
    const recommendedOnly = currentModelFilter === 'recommended';
    const category = (currentModelFilter === 'all' || currentModelFilter === 'recommended')
      ? null
      : currentModelFilter;

    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (recommendedOnly) params.append('recommended_only', 'true');

    const response = await fetch(`${BACKEND_URL}/models/available?${params}`);
    if (!response.ok) {
      throw new Error('Failed to load models');
    }

    const data = await response.json();
    allModels = data.models || [];

    // Load installed models
    await loadInstalledModels();

    // Update stats
    document.getElementById('modelsAvailable').textContent = `${allModels.length} available`;
    document.getElementById('modelsInstalled').textContent = `${installedModels.length} installed`;

    displayModels();
  } catch (error) {
    console.error('Error loading models:', error);
    document.getElementById('modelsList').innerHTML = `
      <div class="empty-state">
        <p>Failed to load models</p>
        <p class="hint">Make sure the backend is running at ${BACKEND_URL}</p>
      </div>
    `;
  }
}

// Load installed models
async function loadInstalledModels() {
  try {
    const response = await fetch(`${BACKEND_URL}/models/installed`);
    if (response.ok) {
      const data = await response.json();
      installedModels = data.models || [];

      // Mark installed models
      allModels.forEach(model => {
        model.installed = installedModels.some(m => m.id === model.id);
      });
    }
  } catch (error) {
    console.warn('Could not load installed models:', error);
  }
}

// Display models in grid
function displayModels() {
  const modelsList = document.getElementById('modelsList');

  if (allModels.length === 0) {
    modelsList.innerHTML = `
      <div class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
        </svg>
        <p>No models found</p>
        <p class="hint">Try a different filter</p>
      </div>
    `;
    return;
  }

  modelsList.innerHTML = allModels.map(model => `
    <div class="model-card ${model.installed ? 'installed' : ''}">
      <div class="model-card-header">
        <div class="model-icon">${getModelIcon(model.category)}</div>
        <div class="model-info">
          <h3 class="model-name">${model.name}</h3>
          <span class="model-category">${model.category}</span>
        </div>
        ${model.recommended ? '<span class="model-badge recommended">⭐ Recommended</span>' : ''}
      </div>
      <p class="model-description">${model.description}</p>
      <div class="model-meta">
        <span class="model-size">📦 ${model.size}</span>
        <span class="model-provider">${model.provider}</span>
      </div>
      ${model.capabilities ? `
        <div class="model-capabilities">
          ${model.capabilities.map(cap => `<span class="capability-tag">${cap}</span>`).join('')}
        </div>
      ` : ''}
      <div class="model-actions">
        <button class="btn-secondary" onclick="showModelDetails('${model.id}')">Details</button>
        ${model.installed
          ? `<button class="btn-danger" onclick="deleteModel('${model.id}')">Delete</button>`
          : `<button class="btn-primary" onclick="downloadModel('${model.id}', '${model.name}')">Download</button>`
        }
      </div>
    </div>
  `).join('');
}

// Get icon for model category
function getModelIcon(category) {
  const icons = {
    'general': '🤖',
    'coding': '💻',
    'chat': '💬',
    'lightweight': '⚡',
    'premium': '⭐'
  };
  return icons[category] || '📦';
}

// Show model details
window.showModelDetails = async function(modelId) {
  try {
    const response = await fetch(`${BACKEND_URL}/models/${encodeURIComponent(modelId)}`);
    const model = await response.json();

    const modal = document.getElementById('modelModal');
    document.getElementById('modelModalTitle').textContent = model.name || model.id;

    document.getElementById('modelModalBody').innerHTML = `
      <p><strong>ID:</strong> ${model.id}</p>
      <p><strong>Provider:</strong> ${model.provider}</p>
      <p><strong>Category:</strong> ${model.category}</p>
      <p><strong>Size:</strong> ${model.size}</p>
      <p><strong>Description:</strong> ${model.description || 'No description'}</p>
      ${model.capabilities ? `
        <p><strong>Capabilities:</strong> ${model.capabilities.join(', ')}</p>
      ` : ''}
      ${model.recommended ? '<p><strong>Status:</strong> <span class="badge-success">Recommended</span></p>' : ''}
      <p><strong>Installed:</strong> ${model.installed ? 'Yes' : 'No'}</p>
    `;

    const actionBtn = document.getElementById('modelModalAction');
    if (model.installed) {
      actionBtn.textContent = 'Delete';
      actionBtn.className = 'btn-danger';
      actionBtn.onclick = async () => {
        await deleteModel(modelId);
        modal.classList.add('hidden');
      };
    } else {
      actionBtn.textContent = 'Download';
      actionBtn.className = 'btn-primary';
      actionBtn.onclick = async () => {
        await downloadModel(modelId, model.name);
        modal.classList.add('hidden');
      };
    }

    modal.classList.remove('hidden');
  } catch (error) {
    console.error('Error loading model details:', error);
    updateStatus('Error loading model details');
  }
};

// Download model
window.downloadModel = async function(modelId, modelName) {
  try {
    // Show download modal
    const downloadModal = document.getElementById('downloadModal');
    document.getElementById('downloadModelName').textContent = modelName;
    document.getElementById('downloadPercent').textContent = '0%';
    document.getElementById('downloadProgressBar').style.width = '0%';
    document.getElementById('downloadSpeed').textContent = '';
    document.getElementById('downloadSize').textContent = '';
    downloadModal.classList.remove('hidden');

    // Start download
    const response = await fetch(`${BACKEND_URL}/models/${encodeURIComponent(modelId)}/download`, {
      method: 'POST'
    });

    if (response.ok) {
      const result = await response.json();
      currentDownload = modelId;
      updateStatus('Download started...');

      // Start polling for progress
      downloadCheckInterval = setInterval(async () => {
        await checkDownloadProgress(modelId);
      }, 1000);
    } else {
      throw new Error('Failed to start download');
    }
  } catch (error) {
    console.error('Error downloading model:', error);
    alert('Error downloading model: ' + error.message);
    document.getElementById('downloadModal').classList.add('hidden');
  }
};

// Check download progress
async function checkDownloadProgress(modelId) {
  try {
    const response = await fetch(`${BACKEND_URL}/models/${encodeURIComponent(modelId)}/download/status`);
    const status = await response.json();

    if (status.status === 'downloading') {
      const percent = status.progress || 0;
      document.getElementById('downloadPercent').textContent = `${percent}%`;
      document.getElementById('downloadProgressBar').style.width = `${percent}%`;

      if (status.downloaded && status.total) {
        const downloaded = (status.downloaded / 1024 / 1024).toFixed(1);
        const total = (status.total / 1024 / 1024).toFixed(1);
        document.getElementById('downloadSize').textContent = `${downloaded} MB / ${total} MB`;
      }
    } else if (status.status === 'completed') {
      // Download complete
      clearInterval(downloadCheckInterval);
      document.getElementById('downloadModal').classList.add('hidden');
      currentDownload = null;
      updateStatus('Model downloaded successfully!');

      // Reload models
      await loadAvailableModelsData();
    } else if (status.status === 'failed') {
      // Download failed
      clearInterval(downloadCheckInterval);
      document.getElementById('downloadModal').classList.add('hidden');
      currentDownload = null;
      updateStatus('Model download failed');
      alert('Download failed. Please try again.');
    }
  } catch (error) {
    console.error('Error checking download progress:', error);
  }
}

// Cancel download
document.getElementById('cancelDownload')?.addEventListener('click', () => {
  if (downloadCheckInterval) {
    clearInterval(downloadCheckInterval);
  }
  document.getElementById('downloadModal').classList.add('hidden');
  currentDownload = null;
  updateStatus('Download cancelled');
});

// Delete model
window.deleteModel = async function(modelId) {
  if (!confirm('Are you sure you want to delete this model? This cannot be undone.')) {
    return;
  }

  try {
    const response = await fetch(`${BACKEND_URL}/models/${encodeURIComponent(modelId)}`, {
      method: 'DELETE'
    });

    if (response.ok) {
      updateStatus('Model deleted successfully');
      await loadAvailableModelsData();
    } else {
      throw new Error('Failed to delete model');
    }
  } catch (error) {
    console.error('Error deleting model:', error);
    alert('Error deleting model: ' + error.message);
  }
};

// Model filter
document.getElementById('modelCategoryFilter')?.addEventListener('change', (e) => {
  currentModelFilter = e.target.value;
  loadAvailableModelsData();
});

// Load models when tab is opened
document.querySelector('[data-tab="models"]')?.addEventListener('click', () => {
  loadAvailableModelsData();
});

// =====================================================================
// Enhanced Settings with Backend Integration
// =====================================================================

// Load settings from backend
async function loadSettingsFromBackend() {
  try {
    const response = await fetch(`${BACKEND_URL}/config`);
    if (response.ok) {
      const config = await response.json();

      // Apply settings to UI
      if (config.theme) {
        themeSelect.value = config.theme;
        applyTheme(config.theme);
      }
      if (config.model) {
        document.getElementById('defaultModel').value = config.model;
      }
      if (config.temperature !== undefined) {
        temperatureInput.value = config.temperature;
        tempValue.textContent = config.temperature;
      }

      updateStatus('Settings loaded from backend');
    }

    // Load update preferences
    const updateResponse = await fetch(`${BACKEND_URL}/updates/preferences`);
    if (updateResponse.ok) {
      const prefs = await updateResponse.json();
      document.getElementById('autoCheck').checked = prefs.auto_check !== false;
      document.getElementById('autoDownload').checked = prefs.auto_download !== false;
      document.getElementById('updateChannel').value = prefs.channel || 'stable';
      document.getElementById('checkInterval').value = prefs.check_interval_hours || 6;
    }

  } catch (error) {
    console.error('Error loading settings from backend:', error);
  }
}

// Save settings to backend
async function saveSettingsToBackend(config) {
  try {
    // Save each config key individually
    for (const [key, value] of Object.entries(config)) {
      const response = await fetch(`${BACKEND_URL}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value })
      });

      if (!response.ok) {
        throw new Error(`Failed to save ${key}`);
      }
    }

    return true;
  } catch (error) {
    console.error('Error saving settings to backend:', error);
    return false;
  }
}

// Override the save settings handler to use backend
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
    // Save to local config (existing functionality)
    await window.winAI.writeConfig(config);

    // Save to backend
    const backendSaved = await saveSettingsToBackend({
      theme: config.ui.theme,
      model: config.model.default,
      temperature: config.model.temperature
    });

    // Save update preferences
    const updatePrefs = {
      auto_check: document.getElementById('autoCheck').checked,
      auto_download: document.getElementById('autoDownload').checked,
      channel: document.getElementById('updateChannel').value,
      check_interval_hours: parseInt(document.getElementById('checkInterval').value)
    };

    const updateResponse = await fetch(`${BACKEND_URL}/updates/preferences`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updatePrefs)
    });

    if (backendSaved && updateResponse.ok) {
      alert('Settings saved successfully!');
      applyTheme(config.ui.theme);
      updateStatus('Settings saved');
    } else {
      alert('Settings saved locally, but some backend settings may not have synced');
    }
  } catch (error) {
    alert('Error saving settings: ' + error.message);
    updateStatus('Error saving settings');
  }
});

// Check for updates now button
document.getElementById('checkNowBtn').addEventListener('click', async () => {
  const btn = document.getElementById('checkNowBtn');
  const statusEl = document.getElementById('updateStatus');

  btn.disabled = true;
  btn.textContent = 'Checking...';
  statusEl.textContent = '';
  statusEl.className = '';

  try {
    const response = await fetch(`${BACKEND_URL}/updates/check`, {
      method: 'POST'
    });

    const data = await response.json();

    if (data.update_available && data.update_info) {
      statusEl.textContent = `Update available: v${data.update_info.version}`;
      statusEl.className = 'info';
      // The update notification will be shown by updater.js
    } else {
      statusEl.textContent = 'You are up to date!';
      statusEl.className = 'success';
    }

  } catch (error) {
    console.error('Error checking for updates:', error);
    statusEl.textContent = 'Error checking for updates';
    statusEl.className = 'error';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Check for Updates Now';
  }
});

// =====================================================================
// Dynamic Model Loading
// =====================================================================

async function loadAvailableModels() {
  try {
    const response = await fetch(`${BACKEND_URL}/models`);
    if (!response.ok) return;

    const data = await response.json();
    const models = data.models || [];

    // Update model select dropdowns
    const modelSelectChat = document.getElementById('modelSelect');
    const modelSelectSettings = document.getElementById('defaultModel');

    const modelOptions = models.map(model =>
      `<option value="${model.id}">${model.name}</option>`
    ).join('');

    if (modelSelectChat) {
      modelSelectChat.innerHTML = modelOptions;
    }
    if (modelSelectSettings) {
      modelSelectSettings.innerHTML = modelOptions;
    }

    updateStatus('Models loaded');
  } catch (error) {
    console.error('Error loading models:', error);
  }
}

// =====================================================================
// Real-time Health Monitoring
// =====================================================================

let healthCheckInterval = null;

async function checkBackendHealth() {
  try {
    const response = await fetch(`${BACKEND_URL}/health`, {
      signal: AbortSignal.timeout(5000)
    });

    if (response.ok) {
      const data = await response.json();

      if (data.status === 'healthy') {
        updateStatus('Connected - Backend healthy');
        return true;
      } else {
        updateStatus('Backend degraded');
        return false;
      }
    } else {
      updateStatus('Backend unreachable');
      return false;
    }
  } catch (error) {
    updateStatus('Backend offline');
    return false;
  }
}

function startHealthMonitoring() {
  // Check health every 30 seconds
  healthCheckInterval = setInterval(checkBackendHealth, 30000);

  // Initial check
  checkBackendHealth();
}

function stopHealthMonitoring() {
  if (healthCheckInterval) {
    clearInterval(healthCheckInterval);
    healthCheckInterval = null;
  }
}

// =====================================================================
// Enhanced Initialization
// =====================================================================

(async () => {
  try {
    // Display environment info
    const env = await window.winAI.envInfo();
    document.getElementById('env').textContent =
      `${env.platform}/${env.arch} • Electron ${env.versions.electron} • Node ${env.versions.node}`;

    // Load config from local file first
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
    updateStatus('Connecting to backend...');
    try {
      const response = await fetch(`${BACKEND_URL}/health`, {
        signal: AbortSignal.timeout(3000)
      });

      if (response.ok) {
        updateStatus('Connected to backend');

        // Load data from backend
        loadConversations();
        loadAvailableModels();
        loadSettingsFromBackend();

        // Start health monitoring
        startHealthMonitoring();
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

// =====================================================================
// Model Management
// =====================================================================

let allModels = [];
let installedModels = [];
let downloadSocket = null;
let currentFilter = 'all';

// Load models on page load
async function loadModels() {
  try {
    // Load available models
    const availableResponse = await fetch(`${BACKEND_URL}/models/available`);
    if (availableResponse.ok) {
      const data = await availableResponse.json();
      allModels = data.models || [];
    }

    // Load installed models
    const installedResponse = await fetch(`${BACKEND_URL}/models/installed`);
    if (installedResponse.ok) {
      const data = await installedResponse.json();
      installedModels = data.models || [];
    }

    // Load system specs and recommendations
    const recsResponse = await fetch(`${BACKEND_URL}/models/recommended`);
    if (recsResponse.ok) {
      const data = await recsResponse.json();
      displaySystemInfo(data.system_specs);
    }

    // Update stats
    updateModelStats();

    // Render models
    renderModels();

  } catch (error) {
    console.error('Error loading models:', error);
    const modelsList = document.getElementById('modelsList');
    if (modelsList) {
      modelsList.innerHTML = `
        <div class="error-state">
          <p>Failed to load models. Make sure the backend is running.</p>
          <button onclick="loadModels()">Retry</button>
        </div>
      `;
    }
  }
}

function updateModelStats() {
  const availableCount = document.getElementById('modelsAvailable');
  const installedCount = document.getElementById('modelsInstalled');

  if (availableCount) {
    availableCount.textContent = `${allModels.length} available`;
  }

  if (installedCount) {
    const installed = allModels.filter(m => m.installed).length;
    installedCount.textContent = `${installed} installed`;
  }
}

function displaySystemInfo(specs) {
  // This could be displayed in a tooltip or info panel
  console.log('System specs:', specs);

  // Add GPU info to UI if available
  if (specs.gpu && specs.gpu.available) {
    const statsDiv = document.querySelector('.models-stats');
    if (statsDiv && !document.getElementById('gpuInfo')) {
      const gpuBadge = document.createElement('span');
      gpuBadge.id = 'gpuInfo';
      gpuBadge.className = 'stat-badge gpu';
      gpuBadge.textContent = `🎮 ${specs.gpu.name}`;
      gpuBadge.title = `GPU Memory: ${specs.gpu.memory_gb}GB`;
      statsDiv.appendChild(gpuBadge);
    }
  }
}

function renderModels() {
  const modelsList = document.getElementById('modelsList');
  if (!modelsList) return;

  const categoryFilter = document.getElementById('modelCategoryFilter');
  const selectedCategory = categoryFilter ? categoryFilter.value : 'all';

  // Filter models
  let filteredModels = allModels;
  if (selectedCategory !== 'all') {
    if (selectedCategory === 'recommended') {
      filteredModels = allModels.filter(m => m.recommended);
    } else {
      filteredModels = allModels.filter(m => m.category === selectedCategory);
    }
  }

  if (filteredModels.length === 0) {
    modelsList.innerHTML = `
      <div class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
        </svg>
        <p>No models found</p>
      </div>
    `;
    return;
  }

  modelsList.innerHTML = filteredModels.map(model => createModelCard(model)).join('');

  // Add event listeners to model cards
  filteredModels.forEach(model => {
    const card = document.getElementById(`model-${model.id.replace(/[:.]/g, '-')}`);
    if (card) {
      card.addEventListener('click', () => showModelDetails(model));
    }
  });
}

function createModelCard(model) {
  const modelId = model.id.replace(/[:.]/g, '-');
  const isInstalled = model.installed || false;
  const suitability = model.suitability || 'good';
  const tier = model.tier || 2;

  // Create badges
  const badges = [];
  if (model.recommended) badges.push('<span class="badge recommended">Recommended</span>');
  if (isInstalled) badges.push('<span class="badge installed">Installed</span>');
  if (tier === 1) badges.push('<span class="badge tier1">Essential</span>');
  if (model.gpu_optimized) badges.push('<span class="badge gpu">GPU Ready</span>');

  return `
    <div id="model-${modelId}" class="model-card ${isInstalled ? 'installed' : ''}" data-suitability="${suitability}">
      <div class="model-header">
        <h3>${model.name}</h3>
        <div class="model-badges">${badges.join('')}</div>
      </div>
      <p class="model-description">${model.description}</p>
      <div class="model-info">
        <span class="model-size">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
          </svg>
          ${model.size}
        </span>
        <span class="model-ram">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="5" width="20" height="14" rx="2"/>
            <path d="M6 9h.01M10 9h.01M14 9h.01M18 9h.01"/>
          </svg>
          ${model.ram_required}
        </span>
        ${model.category ? `<span class="model-category">${model.category}</span>` : ''}
      </div>
      <div class="model-actions">
        ${isInstalled ?
          '<button class="btn-secondary btn-small" onclick="event.stopPropagation(); deleteModel(\'' + model.id + '\')">Delete</button>' :
          '<button class="btn-primary btn-small" onclick="event.stopPropagation(); downloadModel(\'' + model.id + '\')">Download</button>'
        }
      </div>
    </div>
  `;
}

function showModelDetails(model) {
  const modal = document.getElementById('modelModal');
  const modalTitle = document.getElementById('modelModalTitle');
  const modalBody = document.getElementById('modelModalBody');
  const modalAction = document.getElementById('modelModalAction');

  if (!modal) return;

  modalTitle.textContent = model.name;

  modalBody.innerHTML = `
    <div class="model-details">
      <p>${model.description}</p>
      <div class="model-specs">
        <div class="spec-item">
          <strong>Size:</strong> ${model.size}
        </div>
        <div class="spec-item">
          <strong>RAM Required:</strong> ${model.ram_required}
        </div>
        <div class="spec-item">
          <strong>Category:</strong> ${model.category}
        </div>
        <div class="spec-item">
          <strong>Provider:</strong> ${model.provider}
        </div>
        <div class="spec-item">
          <strong>Quantization:</strong> ${model.quantization}
        </div>
        ${model.capabilities ? `
          <div class="spec-item">
            <strong>Capabilities:</strong> ${model.capabilities.join(', ')}
          </div>
        ` : ''}
        ${model.suitability ? `
          <div class="spec-item">
            <strong>Suitability for your system:</strong>
            <span class="suitability-${model.suitability}">${model.suitability}</span>
          </div>
        ` : ''}
      </div>
    </div>
  `;

  if (model.installed) {
    modalAction.textContent = 'Delete';
    modalAction.className = 'btn-secondary';
    modalAction.onclick = () => {
      modal.classList.add('hidden');
      deleteModel(model.id);
    };
  } else {
    modalAction.textContent = 'Download';
    modalAction.className = 'btn-primary';
    modalAction.onclick = () => {
      modal.classList.add('hidden');
      downloadModel(model.id);
    };
  }

  modal.classList.remove('hidden');
}

async function downloadModel(modelId) {
  const downloadModal = document.getElementById('downloadModal');
  const downloadTitle = document.getElementById('downloadModalTitle');
  const downloadModelName = document.getElementById('downloadModelName');
  const downloadPercent = document.getElementById('downloadPercent');
  const downloadProgressBar = document.getElementById('downloadProgressBar');
  const downloadSpeed = document.getElementById('downloadSpeed');
  const downloadSize = document.getElementById('downloadSize');

  if (!downloadModal) return;

  // Find model info
  const model = allModels.find(m => m.id === modelId);
  if (model) {
    downloadModelName.textContent = model.name;
  }

  downloadTitle.textContent = 'Downloading Model';
  downloadPercent.textContent = '0%';
  downloadProgressBar.style.width = '0%';
  downloadSpeed.textContent = 'Initializing...';
  downloadSize.textContent = '';

  downloadModal.classList.remove('hidden');

  // Connect to WebSocket for progress updates
  try {
    if (downloadSocket) {
      downloadSocket.close();
    }

    downloadSocket = new WebSocket(`ws://127.0.0.1:8010/ws/models/download`);

    downloadSocket.onopen = () => {
      console.log('Download WebSocket connected');
      // Request download
      downloadSocket.send(JSON.stringify({
        type: 'download',
        model_id: modelId
      }));
    };

    downloadSocket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'progress') {
        downloadPercent.textContent = `${data.percent}%`;
        downloadProgressBar.style.width = `${data.percent}%`;
        downloadSize.textContent = `${data.downloaded_mb}MB / ${data.total_mb}MB`;
      } else if (data.type === 'complete') {
        downloadPercent.textContent = '100%';
        downloadProgressBar.style.width = '100%';
        downloadSpeed.textContent = 'Complete!';

        setTimeout(() => {
          downloadModal.classList.add('hidden');
          loadModels(); // Refresh model list
        }, 1500);

        if (downloadSocket) {
          downloadSocket.close();
          downloadSocket = null;
        }
      } else if (data.type === 'error') {
        downloadSpeed.textContent = 'Error: ' + data.message;
        console.error('Download error:', data.message);

        setTimeout(() => {
          downloadModal.classList.add('hidden');
        }, 3000);
      }
    };

    downloadSocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      downloadSpeed.textContent = 'Connection error';

      setTimeout(() => {
        downloadModal.classList.add('hidden');
      }, 2000);
    };

    downloadSocket.onclose = () => {
      console.log('Download WebSocket closed');
    };

  } catch (error) {
    console.error('Error starting download:', error);
    alert('Failed to start download: ' + error.message);
    downloadModal.classList.add('hidden');
  }
}

async function deleteModel(modelId) {
  if (!confirm(`Are you sure you want to delete model ${modelId}? This cannot be undone.`)) {
    return;
  }

  try {
    const response = await fetch(`${BACKEND_URL}/models/${modelId}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error('Failed to delete model');
    }

    const result = await response.json();

    if (result.status === 'success') {
      alert('Model deleted successfully');
      loadModels(); // Refresh model list
    } else {
      alert('Error: ' + result.message);
    }

  } catch (error) {
    console.error('Error deleting model:', error);
    alert('Failed to delete model: ' + error.message);
  }
}

// Filter models by category
const modelCategoryFilter = document.getElementById('modelCategoryFilter');
if (modelCategoryFilter) {
  modelCategoryFilter.addEventListener('change', () => {
    renderModels();
  });
}

// Cancel download
const cancelDownload = document.getElementById('cancelDownload');
if (cancelDownload) {
  cancelDownload.addEventListener('click', () => {
    if (downloadSocket) {
      downloadSocket.close();
      downloadSocket = null;
    }
    document.getElementById('downloadModal').classList.add('hidden');
  });
}

// Load models when models tab is opened
const modelsTab = document.querySelector('[data-tab="models"]');
if (modelsTab) {
  modelsTab.addEventListener('click', () => {
    // Delay loading to ensure tab is visible
    setTimeout(() => {
      if (!allModels.length) {
        loadModels();
      }
    }, 100);
  });
}

// Cleanup on window close
window.addEventListener('beforeunload', () => {
  stopHealthMonitoring();
  if (downloadSocket) {
    downloadSocket.close();
  }
});

console.log('Windows AI Renderer initialized');
