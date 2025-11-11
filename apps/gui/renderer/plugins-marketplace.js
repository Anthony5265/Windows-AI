/**
 * Windows AI - Plugin Marketplace
 * Handles plugin discovery, installation, and management in the GUI
 */

// =====================================================================
// Plugin Marketplace State
// =====================================================================

let allPlugins = [];
let filteredPlugins = [];
let currentPluginTab = 'all';
let currentPluginFilter = 'all';
let currentSearchQuery = '';
let selectedPlugin = null;

// =====================================================================
// Plugin Marketplace Initialization
// =====================================================================

/**
 * Initialize plugin marketplace when plugins tab is opened
 */
async function initPluginMarketplace() {
  console.log('Initializing plugin marketplace...');

  // Setup event listeners
  setupPluginEventListeners();

  // Load plugins
  await loadPlugins();
}

/**
 * Setup all event listeners for plugin marketplace
 */
function setupPluginEventListeners() {
  // Search input
  const searchInput = document.getElementById('pluginSearchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      currentSearchQuery = e.target.value;
      filterAndDisplayPlugins();
    });
  }

  // Type filter
  const typeFilter = document.getElementById('pluginTypeFilter');
  if (typeFilter) {
    typeFilter.addEventListener('change', (e) => {
      currentPluginFilter = e.target.value;
      filterAndDisplayPlugins();
    });
  }

  // Refresh button
  const refreshBtn = document.getElementById('refreshPluginsBtn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', loadPlugins);
  }

  // Tab buttons
  const tabButtons = document.querySelectorAll('.plugin-tab-btn');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      tabButtons.forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      currentPluginTab = e.target.dataset.pluginTab;
      filterAndDisplayPlugins();
    });
  });

  // Modal close
  const closeModal = document.getElementById('closePluginModal');
  if (closeModal) {
    closeModal.addEventListener('click', closePluginDetailModal);
  }

  // Plugin actions in modal
  const enableBtn = document.getElementById('pluginEnableBtn');
  const disableBtn = document.getElementById('pluginDisableBtn');

  if (enableBtn) {
    enableBtn.addEventListener('click', () => {
      if (selectedPlugin) {
        enablePlugin(selectedPlugin.id);
      }
    });
  }

  if (disableBtn) {
    disableBtn.addEventListener('click', () => {
      if (selectedPlugin) {
        disablePlugin(selectedPlugin.id);
      }
    });
  }

  // Close modal when clicking outside
  const modal = document.getElementById('pluginDetailModal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closePluginDetailModal();
      }
    });
  }
}

// =====================================================================
// Plugin Loading and Display
// =====================================================================

/**
 * Load all plugins from backend
 */
async function loadPlugins() {
  try {
    updateStatus('Loading plugins...');

    const response = await fetch(`${BACKEND_URL}/plugins`);

    if (response.ok) {
      const data = await response.json();
      allPlugins = data.plugins || [];

      console.log(`Loaded ${allPlugins.length} plugins`);

      // Update stats
      updatePluginStats();

      // Display plugins
      filterAndDisplayPlugins();

      updateStatus(`Loaded ${allPlugins.length} plugins`);
    } else {
      throw new Error('Failed to load plugins');
    }
  } catch (error) {
    console.error('Error loading plugins:', error);
    updateStatus('Error loading plugins', 'error');
    showPluginError('Failed to load plugins. Make sure the backend is running.');
  }
}

/**
 * Filter and display plugins based on current filters
 */
function filterAndDisplayPlugins() {
  // Start with all plugins
  let plugins = [...allPlugins];

  // Apply tab filter
  if (currentPluginTab === 'installed') {
    plugins = plugins.filter(p => p.enabled);
  } else if (currentPluginTab === 'featured') {
    // Featured plugins - could be based on tags or specific IDs
    plugins = plugins.filter(p =>
      p.tags && (p.tags.includes('featured') || p.tags.includes('recommended'))
    );
  }

  // Apply type filter
  if (currentPluginFilter !== 'all') {
    plugins = plugins.filter(p => p.plugin_type === currentPluginFilter);
  }

  // Apply search filter
  if (currentSearchQuery) {
    const query = currentSearchQuery.toLowerCase();
    plugins = plugins.filter(p =>
      p.name.toLowerCase().includes(query) ||
      p.description.toLowerCase().includes(query) ||
      (p.tags && p.tags.some(tag => tag.toLowerCase().includes(query)))
    );
  }

  filteredPlugins = plugins;
  displayPlugins(filteredPlugins);
}

/**
 * Display plugins in the grid
 */
function displayPlugins(plugins) {
  const pluginsList = document.getElementById('pluginsList');

  if (!plugins || plugins.length === 0) {
    pluginsList.innerHTML = `
      <div class="no-plugins">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <p>No plugins found</p>
        <button onclick="loadPlugins()" class="btn-secondary">Refresh</button>
      </div>
    `;
    return;
  }

  // Generate plugin cards
  pluginsList.innerHTML = plugins.map(plugin => createPluginCard(plugin)).join('');

  // Add click handlers
  document.querySelectorAll('.plugin-card').forEach(card => {
    card.addEventListener('click', (e) => {
      // Don't open detail if clicking toggle
      if (e.target.closest('.plugin-toggle')) {
        return;
      }
      const pluginId = card.dataset.pluginId;
      const plugin = allPlugins.find(p => p.id === pluginId);
      if (plugin) {
        showPluginDetail(plugin);
      }
    });
  });

  // Add toggle handlers
  document.querySelectorAll('.plugin-toggle').forEach(toggle => {
    toggle.addEventListener('click', async (e) => {
      e.stopPropagation();
      const pluginId = toggle.dataset.pluginId;
      const enabled = toggle.checked;

      if (enabled) {
        await enablePlugin(pluginId);
      } else {
        await disablePlugin(pluginId);
      }
    });
  });
}

/**
 * Create HTML for a plugin card
 */
function createPluginCard(plugin) {
  const icon = plugin.icon || '🔌';
  const statusClass = plugin.enabled ? 'enabled' : 'disabled';
  const statusText = plugin.enabled ? 'Enabled' : 'Disabled';
  const initializedBadge = plugin.initialized ?
    '<span class="plugin-badge success">Initialized</span>' : '';

  const tags = plugin.tags && plugin.tags.length > 0 ?
    plugin.tags.slice(0, 3).map(tag =>
      `<span class="plugin-tag">${tag}</span>`
    ).join('') : '';

  return `
    <div class="plugin-card ${statusClass}" data-plugin-id="${plugin.id}">
      <div class="plugin-card-header">
        <div class="plugin-icon">${icon}</div>
        <div class="plugin-toggle-wrapper">
          <label class="toggle-switch">
            <input
              type="checkbox"
              class="plugin-toggle"
              data-plugin-id="${plugin.id}"
              ${plugin.enabled ? 'checked' : ''}
            />
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>
      <div class="plugin-card-body">
        <h3 class="plugin-name">${plugin.name}</h3>
        <p class="plugin-description">${truncate(plugin.description, 100)}</p>
        <div class="plugin-meta">
          <span class="plugin-type">${plugin.plugin_type}</span>
          <span class="plugin-version">v${plugin.version}</span>
        </div>
        ${tags ? `<div class="plugin-tags-preview">${tags}</div>` : ''}
        <div class="plugin-status">
          <span class="status-dot ${statusClass}"></span>
          <span class="status-text">${statusText}</span>
          ${initializedBadge}
        </div>
      </div>
    </div>
  `;
}

/**
 * Update plugin statistics
 */
function updatePluginStats() {
  const totalCount = allPlugins.length;
  const activeCount = allPlugins.filter(p => p.enabled).length;

  document.getElementById('pluginsCount').textContent = `${totalCount} plugins`;
  document.getElementById('pluginsActive').textContent = `${activeCount} active`;
}

// =====================================================================
// Plugin Detail Modal
// =====================================================================

/**
 * Show plugin detail modal
 */
function showPluginDetail(plugin) {
  selectedPlugin = plugin;

  // Update modal content
  document.getElementById('pluginDetailIcon').textContent = plugin.icon || '🔌';
  document.getElementById('pluginDetailName').textContent = plugin.name;
  document.getElementById('pluginDetailAuthor').textContent = plugin.author || 'Unknown';
  document.getElementById('pluginDetailVersion').textContent = `v${plugin.version}`;
  document.getElementById('pluginDetailType').textContent = plugin.plugin_type;
  document.getElementById('pluginDetailDescription').textContent = plugin.description;

  // Update status
  const statusEl = document.getElementById('pluginDetailStatus');
  const statusClass = plugin.enabled ? 'enabled' : 'disabled';
  const statusText = plugin.enabled ? 'Enabled' : 'Disabled';
  statusEl.className = `plugin-detail-status ${statusClass}`;
  statusEl.querySelector('.status-text').textContent = statusText;

  // Update action buttons
  const enableBtn = document.getElementById('pluginEnableBtn');
  const disableBtn = document.getElementById('pluginDisableBtn');

  if (plugin.enabled) {
    enableBtn.style.display = 'none';
    disableBtn.style.display = 'block';
  } else {
    enableBtn.style.display = 'block';
    disableBtn.style.display = 'none';
  }

  // Features (extract from description or use predefined)
  const featuresEl = document.getElementById('pluginDetailFeatures');
  featuresEl.innerHTML = '<li>Advanced functionality</li><li>Easy to use</li><li>Reliable performance</li>';

  // Requirements
  if (plugin.requirements && plugin.requirements.length > 0) {
    document.getElementById('pluginDetailRequirementsSection').style.display = 'block';
    document.getElementById('pluginDetailRequirements').innerHTML =
      plugin.requirements.map(req => `<div class="requirement-item">${req}</div>`).join('');
  } else {
    document.getElementById('pluginDetailRequirementsSection').style.display = 'none';
  }

  // Tags
  if (plugin.tags && plugin.tags.length > 0) {
    document.getElementById('pluginDetailTagsSection').style.display = 'block';
    document.getElementById('pluginDetailTags').innerHTML =
      plugin.tags.map(tag => `<span class="plugin-tag">${tag}</span>`).join('');
  } else {
    document.getElementById('pluginDetailTagsSection').style.display = 'none';
  }

  // Show modal
  document.getElementById('pluginDetailModal').style.display = 'flex';
}

/**
 * Close plugin detail modal
 */
function closePluginDetailModal() {
  document.getElementById('pluginDetailModal').style.display = 'none';
  selectedPlugin = null;
}

// =====================================================================
// Plugin Actions
// =====================================================================

/**
 * Enable a plugin
 */
async function enablePlugin(pluginId) {
  try {
    updateStatus(`Enabling plugin...`);

    const response = await fetch(`${BACKEND_URL}/plugins/${pluginId}/enable`, {
      method: 'POST'
    });

    if (response.ok) {
      const data = await response.json();
      updateStatus(`Plugin enabled: ${pluginId}`);

      // Refresh plugins
      await loadPlugins();

      // Update modal if showing this plugin
      if (selectedPlugin && selectedPlugin.id === pluginId) {
        const updatedPlugin = allPlugins.find(p => p.id === pluginId);
        if (updatedPlugin) {
          showPluginDetail(updatedPlugin);
        }
      }

      showNotification('Plugin enabled successfully', 'success');
    } else {
      throw new Error('Failed to enable plugin');
    }
  } catch (error) {
    console.error('Error enabling plugin:', error);
    updateStatus('Error enabling plugin', 'error');
    showNotification('Failed to enable plugin', 'error');
  }
}

/**
 * Disable a plugin
 */
async function disablePlugin(pluginId) {
  try {
    updateStatus(`Disabling plugin...`);

    const response = await fetch(`${BACKEND_URL}/plugins/${pluginId}/disable`, {
      method: 'POST'
    });

    if (response.ok) {
      const data = await response.json();
      updateStatus(`Plugin disabled: ${pluginId}`);

      // Refresh plugins
      await loadPlugins();

      // Update modal if showing this plugin
      if (selectedPlugin && selectedPlugin.id === pluginId) {
        const updatedPlugin = allPlugins.find(p => p.id === pluginId);
        if (updatedPlugin) {
          showPluginDetail(updatedPlugin);
        }
      }

      showNotification('Plugin disabled successfully', 'success');
    } else {
      throw new Error('Failed to disable plugin');
    }
  } catch (error) {
    console.error('Error disabling plugin:', error);
    updateStatus('Error disabling plugin', 'error');
    showNotification('Failed to disable plugin', 'error');
  }
}

// =====================================================================
// Utilities
// =====================================================================

/**
 * Truncate text to specified length
 */
function truncate(text, length) {
  if (!text) return '';
  if (text.length <= length) return text;
  return text.substring(0, length) + '...';
}

/**
 * Show error message in plugins list
 */
function showPluginError(message) {
  const pluginsList = document.getElementById('pluginsList');
  pluginsList.innerHTML = `
    <div class="error-message">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <p>${message}</p>
      <button onclick="loadPlugins()" class="btn-primary">Retry</button>
    </div>
  `;
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'info') {
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.textContent = message;

  // Add to page
  document.body.appendChild(notification);

  // Show notification
  setTimeout(() => {
    notification.classList.add('show');
  }, 100);

  // Remove notification after 3 seconds
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 3000);
}

// =====================================================================
// Initialize when plugins tab is activated
// =====================================================================

// Watch for plugins tab activation
document.addEventListener('DOMContentLoaded', () => {
  const pluginsTab = document.querySelector('[data-tab="plugins"]');
  if (pluginsTab) {
    pluginsTab.addEventListener('click', () => {
      // Only initialize once
      if (allPlugins.length === 0) {
        initPluginMarketplace();
      }
    });
  }

  // Initialize immediately if plugins tab is active
  if (document.getElementById('plugins').classList.contains('active')) {
    initPluginMarketplace();
  }
});

// Export functions for use in renderer.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    initPluginMarketplace,
    loadPlugins,
    enablePlugin,
    disablePlugin
  };
}
