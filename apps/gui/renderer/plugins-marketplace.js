/**
 * Windows AI - Plugin Marketplace
 * GUI integration for the backend marketplace API.
 */

let marketplacePlugins = [];
let filteredMarketplacePlugins = [];
let marketplaceCategories = [];
let currentPluginTab = 'all';
let currentPluginFilter = 'all';
let currentSearchQuery = '';
let currentPluginSort = 'name_asc';
let selectedPlugin = null;
let pluginMarketplaceInitialized = false;

function getMarketplaceBaseUrl() {
  return `${BACKEND_URL}/api/marketplace`;
}

async function initPluginMarketplace() {
  if (pluginMarketplaceInitialized) {
    await Promise.all([loadMarketplaceCategories(), loadPlugins()]);
    return;
  }

  pluginMarketplaceInitialized = true;
  setupPluginEventListeners();
  await Promise.all([loadMarketplaceCategories(), loadPlugins()]);
}

function setupPluginEventListeners() {
  const searchInput = document.getElementById('pluginSearchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      currentSearchQuery = e.target.value.trim();
      filterAndDisplayPlugins();
    });
  }

  const typeFilter = document.getElementById('pluginTypeFilter');
  if (typeFilter) {
    typeFilter.addEventListener('change', (e) => {
      currentPluginFilter = e.target.value;
      filterAndDisplayPlugins();
    });
  }

  const sortFilter = document.getElementById('pluginSortFilter');
  if (sortFilter) {
    sortFilter.addEventListener('change', (e) => {
      currentPluginSort = e.target.value;
      filterAndDisplayPlugins();
    });
  }

  const refreshBtn = document.getElementById('refreshPluginsBtn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
      await Promise.all([loadMarketplaceCategories(), loadPlugins()]);
    });
  }

  document.querySelectorAll('.plugin-tab-btn').forEach((btn) => {
    btn.addEventListener('click', (event) => {
      document.querySelectorAll('.plugin-tab-btn').forEach((tabBtn) => tabBtn.classList.remove('active'));
      event.currentTarget.classList.add('active');
      currentPluginTab = event.currentTarget.dataset.pluginTab || 'all';
      filterAndDisplayPlugins();
    });
  });

  const closeModal = document.getElementById('closePluginModal');
  if (closeModal) {
    closeModal.addEventListener('click', closePluginDetailModal);
  }

  const modal = document.getElementById('pluginDetailModal');
  if (modal) {
    modal.addEventListener('click', (event) => {
      if (event.target === modal) {
        closePluginDetailModal();
      }
    });
  }

  const primaryActionBtn = document.getElementById('pluginEnableBtn');
  const secondaryActionBtn = document.getElementById('pluginDisableBtn');

  if (primaryActionBtn) {
    primaryActionBtn.addEventListener('click', async () => {
      if (!selectedPlugin) return;
      await installPlugin(selectedPlugin.id);
    });
  }

  if (secondaryActionBtn) {
    secondaryActionBtn.addEventListener('click', async () => {
      if (!selectedPlugin) return;
      await uninstallPlugin(selectedPlugin.id);
    });
  }
}

async function loadMarketplaceCategories() {
  try {
    const response = await fetch(`${getMarketplaceBaseUrl()}/categories`);
    if (!response.ok) {
      throw new Error(`Failed to load categories (${response.status})`);
    }

    const data = await response.json();
    marketplaceCategories = Array.isArray(data.categories) ? data.categories : [];
    populateCategoryFilter();
  } catch (error) {
    console.error('Error loading marketplace categories:', error);
  }
}

function populateCategoryFilter() {
  const filter = document.getElementById('pluginTypeFilter');
  if (!filter) return;

  const currentValue = currentPluginFilter;
  filter.innerHTML = [
    '<option value="all">All Categories</option>',
    ...marketplaceCategories.map((category) => {
      const label = `${formatCategoryName(category.name)} (${category.count})`;
      return `<option value="${escapeHtml(category.name)}">${escapeHtml(label)}</option>`;
    })
  ].join('');

  if ([ 'all', ...marketplaceCategories.map((category) => category.name) ].includes(currentValue)) {
    filter.value = currentValue;
  } else {
    currentPluginFilter = 'all';
    filter.value = 'all';
  }
}

async function loadPlugins() {
  try {
    updateStatus('Loading plugin marketplace...');

    const response = await fetch(`${getMarketplaceBaseUrl()}/?page=1&per_page=500`);
    if (!response.ok) {
      throw new Error(`Failed to load plugins (${response.status})`);
    }

    const data = await response.json();
    marketplacePlugins = Array.isArray(data) ? data : [];
    updatePluginStats();
    filterAndDisplayPlugins();
    updateStatus(`Loaded ${marketplacePlugins.length} marketplace plugins`);
  } catch (error) {
    console.error('Error loading plugins:', error);
    updateStatus('Error loading plugin marketplace');
    showPluginError('Failed to load plugin marketplace. Make sure the backend is running.');
  }
}

function filterAndDisplayPlugins() {
  let plugins = [...marketplacePlugins];

  if (currentPluginTab === 'installed') {
    plugins = plugins.filter((plugin) => Boolean(plugin.installed));
  } else if (currentPluginTab === 'featured') {
    plugins = plugins.filter((plugin) => {
      const tags = plugin.tags || [];
      return (
        tags.includes('featured') ||
        tags.includes('recommended') ||
        plugin.rating >= 4.5 ||
        plugin.downloads >= 100
      );
    });
  }

  if (currentPluginFilter !== 'all') {
    plugins = plugins.filter((plugin) => plugin.category === currentPluginFilter);
  }

  if (currentSearchQuery) {
    const query = currentSearchQuery.toLowerCase();
    plugins = plugins.filter((plugin) => {
      const searchable = [
        plugin.name,
        plugin.id,
        plugin.description,
        plugin.author,
        plugin.category,
        ...(plugin.tags || [])
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return searchable.includes(query);
    });
  }

  filteredMarketplacePlugins = sortPlugins(plugins);
  displayPlugins(filteredMarketplacePlugins);
}

function sortPlugins(plugins) {
  const sorted = [...plugins];

  switch (currentPluginSort) {
    case 'name_desc':
      sorted.sort((a, b) => safeLabel(b).localeCompare(safeLabel(a)));
      break;
    case 'enabled_first':
      sorted.sort((a, b) => Number(Boolean(b.installed)) - Number(Boolean(a.installed)) || safeLabel(a).localeCompare(safeLabel(b)));
      break;
    case 'newest':
      sorted.sort((a, b) => (b.version || '0').localeCompare(a.version || '0', undefined, { numeric: true }));
      break;
    default:
      sorted.sort((a, b) => safeLabel(a).localeCompare(safeLabel(b)));
      break;
  }

  return sorted;
}

function displayPlugins(plugins) {
  const pluginsList = document.getElementById('pluginsList');
  if (!pluginsList) return;

  const visibleBadge = document.getElementById('pluginsVisible');
  if (visibleBadge) {
    visibleBadge.textContent = `${plugins.length} shown`;
  }

  if (!plugins.length) {
    pluginsList.innerHTML = `
      <div class="no-plugins">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <p>No plugins found</p>
        <button class="btn-secondary" id="retryMarketplaceLoadBtn">Refresh</button>
      </div>
    `;

    const retryBtn = document.getElementById('retryMarketplaceLoadBtn');
    retryBtn?.addEventListener('click', loadPlugins);
    return;
  }

  pluginsList.innerHTML = plugins.map(createPluginCard).join('');

  document.querySelectorAll('.plugin-card').forEach((card) => {
    card.addEventListener('click', (event) => {
      if (event.target.closest('.plugin-action-btn')) return;
      const pluginId = card.dataset.pluginId;
      const plugin = marketplacePlugins.find((item) => item.id === pluginId);
      if (plugin) {
        showPluginDetail(plugin);
      }
    });
  });

  document.querySelectorAll('.plugin-primary-action').forEach((button) => {
    button.addEventListener('click', async (event) => {
      event.stopPropagation();
      const pluginId = button.dataset.pluginId;
      const plugin = marketplacePlugins.find((item) => item.id === pluginId);
      if (!plugin) return;

      if (plugin.installed) {
        await uninstallPlugin(pluginId);
      } else {
        await installPlugin(pluginId);
      }
    });
  });

  document.querySelectorAll('.plugin-secondary-action').forEach((button) => {
    button.addEventListener('click', async (event) => {
      event.stopPropagation();
      const pluginId = button.dataset.pluginId;
      const plugin = marketplacePlugins.find((item) => item.id === pluginId);
      if (!plugin) return;
      showPluginDetail(plugin);
    });
  });
}

function createPluginCard(plugin) {
  const icon = getPluginIcon(plugin.category);
  const statusClass = plugin.installed ? 'enabled' : 'disabled';
  const statusText = plugin.installed ? 'Installed' : 'Available';
  const primaryActionLabel = plugin.installed ? 'Remove' : 'Install';
  const topTags = (plugin.tags || []).slice(0, 3);

  return `
    <div class="plugin-card ${statusClass}" data-plugin-id="${escapeHtml(plugin.id)}">
      <div class="plugin-card-header">
        <div class="plugin-icon">${icon}</div>
        <div class="plugin-toggle-wrapper">
          <button class="btn-small ${plugin.installed ? 'btn-secondary' : 'btn-primary'} plugin-action-btn plugin-primary-action" data-plugin-id="${escapeHtml(plugin.id)}">
            ${primaryActionLabel}
          </button>
        </div>
      </div>
      <div class="plugin-card-body">
        <h3 class="plugin-name">${escapeHtml(plugin.name || plugin.id)}</h3>
        <p class="plugin-description">${escapeHtml(truncate(plugin.description || 'No description available', 120))}</p>
        <div class="plugin-meta">
          <span class="plugin-type">${escapeHtml(formatCategoryName(plugin.category || 'general'))}</span>
          <span class="plugin-version">v${escapeHtml(plugin.version || '1.0.0')}</span>
        </div>
        <div class="plugin-meta">
          <span>⬇ ${Number(plugin.downloads || 0).toLocaleString()}</span>
          <span>★ ${formatRating(plugin.rating)}</span>
        </div>
        ${topTags.length ? `<div class="plugin-tags-preview">${topTags.map((tag) => `<span class="plugin-tag">${escapeHtml(tag)}</span>`).join('')}</div>` : ''}
        <div class="plugin-status">
          <span class="status-dot ${statusClass}"></span>
          <span class="status-text">${statusText}</span>
        </div>
        <div class="plugin-actions">
          <button class="btn-secondary plugin-action-btn plugin-secondary-action" data-plugin-id="${escapeHtml(plugin.id)}">Details</button>
        </div>
      </div>
    </div>
  `;
}

function updatePluginStats() {
  const totalCount = marketplacePlugins.length;
  const installedCount = marketplacePlugins.filter((plugin) => Boolean(plugin.installed)).length;

  const totalEl = document.getElementById('pluginsCount');
  const activeEl = document.getElementById('pluginsActive');
  const visibleEl = document.getElementById('pluginsVisible');

  if (totalEl) totalEl.textContent = `${totalCount} plugins`;
  if (activeEl) activeEl.textContent = `${installedCount} installed`;
  if (visibleEl) visibleEl.textContent = `${filteredMarketplacePlugins.length || totalCount} shown`;
}

function showPluginDetail(plugin) {
  selectedPlugin = plugin;

  document.getElementById('pluginDetailIcon').textContent = getPluginIcon(plugin.category);
  document.getElementById('pluginDetailName').textContent = plugin.name || plugin.id;
  document.getElementById('pluginDetailAuthor').textContent = plugin.author || 'Windows AI Team';
  document.getElementById('pluginDetailVersion').textContent = `v${plugin.version || '1.0.0'}`;
  document.getElementById('pluginDetailType').textContent = formatCategoryName(plugin.category || 'general');
  document.getElementById('pluginDetailDescription').textContent = plugin.description || 'No description available.';

  const statusEl = document.getElementById('pluginDetailStatus');
  const installed = Boolean(plugin.installed);
  statusEl.className = `plugin-detail-status ${installed ? 'enabled' : 'disabled'}`;
  statusEl.querySelector('.status-text').textContent = installed ? 'Installed' : 'Available';

  const enableBtn = document.getElementById('pluginEnableBtn');
  const disableBtn = document.getElementById('pluginDisableBtn');
  if (enableBtn) {
    enableBtn.style.display = installed ? 'none' : 'inline-flex';
    enableBtn.textContent = 'Install';
  }
  if (disableBtn) {
    disableBtn.style.display = installed ? 'inline-flex' : 'none';
    disableBtn.textContent = 'Remove';
  }

  const featuresEl = document.getElementById('pluginDetailFeatures');
  featuresEl.innerHTML = [
    `<li>Category: ${escapeHtml(formatCategoryName(plugin.category || 'general'))}</li>`,
    `<li>Author: ${escapeHtml(plugin.author || 'Windows AI Team')}</li>`,
    `<li>Downloads: ${Number(plugin.downloads || 0).toLocaleString()}</li>`,
    `<li>Rating: ${formatRating(plugin.rating)}</li>`
  ].join('');

  const requirementsSection = document.getElementById('pluginDetailRequirementsSection');
  const requirementsEl = document.getElementById('pluginDetailRequirements');
  requirementsSection.style.display = 'block';
  requirementsEl.innerHTML = `
    <div class="requirement-item">Windows AI backend running</div>
    <div class="requirement-item">Marketplace API available</div>
    <div class="requirement-item">Plugin id: ${escapeHtml(plugin.id)}</div>
  `;

  const tagsSection = document.getElementById('pluginDetailTagsSection');
  const tagsEl = document.getElementById('pluginDetailTags');
  const tags = plugin.tags || [];
  if (tags.length) {
    tagsSection.style.display = 'block';
    tagsEl.innerHTML = tags.map((tag) => `<span class="plugin-tag">${escapeHtml(tag)}</span>`).join('');
  } else {
    tagsSection.style.display = 'none';
    tagsEl.innerHTML = '';
  }

  document.getElementById('pluginDetailModal').style.display = 'flex';
}

function closePluginDetailModal() {
  const modal = document.getElementById('pluginDetailModal');
  if (modal) {
    modal.style.display = 'none';
  }
  selectedPlugin = null;
}

async function installPlugin(pluginId) {
  try {
    updateStatus(`Installing ${pluginId}...`);
    const response = await fetch(`${getMarketplaceBaseUrl()}/install`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plugin_id: pluginId })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to install plugin (${response.status})`);
    }

    showNotification('Plugin installed successfully', 'success');
    await loadPlugins();
    const updatedPlugin = marketplacePlugins.find((plugin) => plugin.id === pluginId);
    if (selectedPlugin && updatedPlugin) {
      showPluginDetail(updatedPlugin);
    }
    updateStatus(`Installed ${pluginId}`);
  } catch (error) {
    console.error('Error installing plugin:', error);
    updateStatus('Plugin install failed');
    showNotification(error.message || 'Failed to install plugin', 'error');
  }
}

async function uninstallPlugin(pluginId) {
  try {
    updateStatus(`Removing ${pluginId}...`);
    const response = await fetch(`${getMarketplaceBaseUrl()}/uninstall/${encodeURIComponent(pluginId)}`, {
      method: 'POST'
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to remove plugin (${response.status})`);
    }

    const result = await response.json().catch(() => ({}));
    const isInfo = result.status === 'info';
    showNotification(result.message || (isInfo ? 'Plugin cannot be removed' : 'Plugin removed successfully'), isInfo ? 'info' : 'success');
    await loadPlugins();
    const updatedPlugin = marketplacePlugins.find((plugin) => plugin.id === pluginId);
    if (selectedPlugin && updatedPlugin) {
      showPluginDetail(updatedPlugin);
    }
    updateStatus(result.message || `Removed ${pluginId}`);
  } catch (error) {
    console.error('Error removing plugin:', error);
    updateStatus('Plugin removal failed');
    showNotification(error.message || 'Failed to remove plugin', 'error');
  }
}

function getPluginIcon(category) {
  const icons = {
    windows: '🪟',
    windows_os: '🖥️',
    audio_models: '🎵',
    vision_models: '👁️',
    code_models: '💻',
    cloud: '☁️',
    creative: '🎨',
    finance: '💹',
    gaming: '🎮',
    health: '🩺',
    general: '🔌'
  };
  return icons[category] || '🔌';
}

function formatCategoryName(category) {
  return String(category || 'general')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatRating(rating) {
  const value = Number(rating || 0);
  return value > 0 ? value.toFixed(1) : 'New';
}

function safeLabel(plugin) {
  return plugin.name || plugin.id || 'Unnamed Plugin';
}

function truncate(text, length) {
  if (!text) return '';
  return text.length <= length ? text : `${text.slice(0, length)}...`;
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function showPluginError(message) {
  const pluginsList = document.getElementById('pluginsList');
  if (!pluginsList) return;
  pluginsList.innerHTML = `
    <div class="error-message">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <p>${escapeHtml(message)}</p>
      <button class="btn-primary" id="retryMarketplaceErrorBtn">Retry</button>
    </div>
  `;

  const retryBtn = document.getElementById('retryMarketplaceErrorBtn');
  retryBtn?.addEventListener('click', loadPlugins);
}

function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  document.body.appendChild(notification);

  requestAnimationFrame(() => notification.classList.add('show'));
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

document.addEventListener('DOMContentLoaded', () => {
  const pluginsTab = document.querySelector('[data-tab="plugins"]');
  pluginsTab?.addEventListener('click', () => {
    initPluginMarketplace();
  });

  if (document.getElementById('plugins')?.classList.contains('active')) {
    initPluginMarketplace();
  }
});

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    initPluginMarketplace,
    loadPlugins,
    installPlugin,
    uninstallPlugin
  };
}
