/**
 * Windows AI - Renderer Process JavaScript
 *
 * Handles UI interactions and communication with main process
 */

// State
let apiUrl = '';
let allPlugins = [];
let systemInfo = null;

// Initialize app
async function init() {
    console.log('Initializing Windows AI...');

    // Get API URL
    try {
        apiUrl = await window.windowsAI.getApiUrl();
        console.log('API URL:', apiUrl);
        updateStatus('Connected', true);
    } catch (error) {
        console.error('Failed to get API URL:', error);
        updateStatus('Disconnected', false);
        return;
    }

    // Load environment info
    loadEnvironmentInfo();

    // Setup event listeners
    setupEventListeners();

    // Load initial data
    await refreshData();
}

// Update status indicator
function updateStatus(text, connected) {
    const statusText = document.getElementById('status-text');
    const statusIndicator = document.querySelector('.status-indicator');

    statusText.textContent = text;

    if (connected) {
        statusIndicator.style.background = 'var(--success)';
    } else {
        statusIndicator.style.background = 'var(--danger)';
    }
}

// Load environment information
function loadEnvironmentInfo() {
    const versions = window.windowsAI.versions;

    document.getElementById('node-version').textContent = versions.node;
    document.getElementById('chrome-version').textContent = versions.chrome;
    document.getElementById('electron-version').textContent = versions.electron;
}

// Setup event listeners
function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(button => {
        button.addEventListener('click', () => {
            const view = button.getAttribute('data-view');
            switchView(view);
        });
    });

    // Plugin search
    const searchInput = document.getElementById('plugin-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            filterPlugins(e.target.value);
        });
    }

    // Category filter
    const categoryFilter = document.getElementById('category-filter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', (e) => {
            filterPluginsByCategory(e.target.value);
        });
    }

    // Modal close on background click
    document.getElementById('plugin-modal').addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            closeModal();
        }
    });
}

// Switch view
function switchView(viewName) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-view="${viewName}"]`).classList.add('active');

    // Update views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById(`view-${viewName}`).classList.add('active');

    // Load view-specific data
    if (viewName === 'settings') {
        loadSystemInfo();
    }
}

// Refresh all data
async function refreshData() {
    console.log('Refreshing data...');

    try {
        // Load plugins
        await loadPlugins();

        // Load system info for dashboard
        await loadSystemInfo();

        updateStatus('Connected', true);
    } catch (error) {
        console.error('Error refreshing data:', error);
        updateStatus('Error', false);
    }
}

// Load plugins
async function loadPlugins() {
    try {
        const data = await window.windowsAI.getPlugins();
        allPlugins = data.plugins || [];

        console.log(`Loaded ${allPlugins.length} plugins`);

        // Update counts
        document.getElementById('plugin-count').textContent = allPlugins.length;
        document.getElementById('active-count').textContent = allPlugins.length;
        document.getElementById('total-plugins').textContent = allPlugins.length;

        // Render plugins list
        renderPlugins(allPlugins);

        // Update categories
        if (data.categories) {
            renderCategories(data.categories);
            populateCategoryFilter(data.categories);
            document.getElementById('categories-count').textContent = Object.keys(data.categories).length;
        }

        return data;
    } catch (error) {
        console.error('Error loading plugins:', error);
        document.getElementById('plugins-list').innerHTML = '<p class="placeholder">Failed to load plugins</p>';
        throw error;
    }
}

// Render plugins
function renderPlugins(plugins) {
    const container = document.getElementById('plugins-list');

    if (plugins.length === 0) {
        container.innerHTML = '<p class="placeholder">No plugins found</p>';
        return;
    }

    container.innerHTML = plugins.map(plugin => `
        <div class="plugin-card" onclick="showPluginDetail('${plugin.id}')">
            <div class="plugin-header">
                <div class="plugin-name">${escapeHtml(plugin.name)}</div>
                <div class="plugin-type">${escapeHtml(plugin.plugin_type)}</div>
            </div>
            <div class="plugin-description">${escapeHtml(plugin.description)}</div>
            <div class="plugin-tags">
                ${plugin.tags.map(tag => `<span class="plugin-tag">${escapeHtml(tag)}</span>`).join('')}
            </div>
        </div>
    `).join('');
}

// Render categories
function renderCategories(categories) {
    const container = document.getElementById('categories-list');

    const categoryHtml = Object.entries(categories)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 20) // Top 20 categories
        .map(([name, count]) => `
            <span class="category-badge">
                ${escapeHtml(name)}
                <span class="category-count">${count}</span>
            </span>
        `).join('');

    container.innerHTML = categoryHtml || '<p class="placeholder">No categories</p>';
}

// Populate category filter
function populateCategoryFilter(categories) {
    const select = document.getElementById('category-filter');

    const options = Object.keys(categories)
        .sort()
        .map(cat => `<option value="${escapeHtml(cat)}">${escapeHtml(cat)}</option>`)
        .join('');

    select.innerHTML = '<option value="">All Categories</option>' + options;
}

// Filter plugins by search
function filterPlugins(searchTerm) {
    const filtered = allPlugins.filter(plugin => {
        const term = searchTerm.toLowerCase();
        return plugin.name.toLowerCase().includes(term) ||
               plugin.description.toLowerCase().includes(term) ||
               plugin.tags.some(tag => tag.toLowerCase().includes(term));
    });

    renderPlugins(filtered);
}

// Filter plugins by category
function filterPluginsByCategory(category) {
    if (!category) {
        renderPlugins(allPlugins);
        return;
    }

    const filtered = allPlugins.filter(plugin =>
        plugin.tags.some(tag => tag.toLowerCase() === category.toLowerCase())
    );

    renderPlugins(filtered);
}

// Show plugin detail modal
function showPluginDetail(pluginId) {
    const plugin = allPlugins.find(p => p.id === pluginId);
    if (!plugin) return;

    const modal = document.getElementById('plugin-modal');
    const title = document.getElementById('modal-plugin-name');
    const body = document.getElementById('modal-body');

    title.textContent = plugin.name;

    body.innerHTML = `
        <div class="info-grid">
            <div class="info-item">
                <span class="info-label">ID</span>
                <span class="info-value">${escapeHtml(plugin.id)}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Type</span>
                <span class="info-value">${escapeHtml(plugin.plugin_type)}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Version</span>
                <span class="info-value">${escapeHtml(plugin.version)}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Author</span>
                <span class="info-value">${escapeHtml(plugin.author)}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Status</span>
                <span class="info-value">${escapeHtml(plugin.status)}</span>
            </div>
        </div>

        <div style="margin-top: 20px;">
            <h4 style="margin-bottom: 10px;">Description</h4>
            <p style="color: var(--text-secondary); line-height: 1.6;">
                ${escapeHtml(plugin.description)}
            </p>
        </div>

        <div style="margin-top: 20px;">
            <h4 style="margin-bottom: 10px;">Tags</h4>
            <div class="plugin-tags">
                ${plugin.tags.map(tag => `<span class="plugin-tag">${escapeHtml(tag)}</span>`).join('')}
            </div>
        </div>

        <div style="margin-top: 20px;">
            <button class="action-btn" onclick="testPlugin('${escapeHtml(plugin.id)}')">
                Test Plugin
            </button>
        </div>
    `;

    modal.classList.add('active');
}

// Close modal
function closeModal() {
    document.getElementById('plugin-modal').classList.remove('active');
}

// Test plugin (placeholder)
async function testPlugin(pluginId) {
    console.log('Testing plugin:', pluginId);
    alert(`Testing ${pluginId}...\n\nPlugin execution interface coming soon!`);
}

// Load system info
async function loadSystemInfo() {
    try {
        systemInfo = await window.windowsAI.getSystemInfo();
        console.log('System info:', systemInfo);

        // Update uptime
        if (systemInfo.uptime) {
            const uptime = Math.floor(systemInfo.uptime);
            document.getElementById('uptime').textContent = formatUptime(uptime);
        }

        // Render system info in settings
        const container = document.getElementById('system-info');
        container.innerHTML = `
            <div class="info-item">
                <span class="info-label">Name</span>
                <span class="info-value">${escapeHtml(systemInfo.name)}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Version</span>
                <span class="info-value">${escapeHtml(systemInfo.version)}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Status</span>
                <span class="info-value">${escapeHtml(systemInfo.status)}</span>
            </div>
            <div class="info-item">
                <span class="info-label">API Version</span>
                <span class="info-value">${escapeHtml(systemInfo.api_version)}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Uptime</span>
                <span class="info-value">${formatUptime(Math.floor(systemInfo.uptime))}</span>
            </div>
        `;

    } catch (error) {
        console.error('Error loading system info:', error);
    }
}

// Open API docs
function openApiDocs() {
    require('electron').shell.openExternal(apiUrl + '/docs');
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatUptime(seconds) {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}

// Make functions globally available
window.switchView = switchView;
window.refreshData = refreshData;
window.openApiDocs = openApiDocs;
window.closeModal = closeModal;
window.showPluginDetail = showPluginDetail;
window.testPlugin = testPlugin;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

console.log('Windows AI app.js loaded');
