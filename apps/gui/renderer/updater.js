/**
 * Windows AI - Auto-Update Module
 * Handles update checking, notifications, and installation
 */

const BACKEND_URL = 'http://127.0.0.1:8010';
const GITHUB_RELEASE_MANIFEST_URL = 'https://github.com/Anthony5265/Windows-AI/releases/latest/download/latest-release.json';
const FALLBACK_CURRENT_VERSION = '0.5.0';

class UpdateManager {
  constructor() {
    this.updateStatus = null;
    this.checkInterval = null;
    this.isNotificationVisible = false;
  }

  /**
   * Initialize update system
   */
  async initialize() {
    console.log('[Updater] Initializing update system...');

    try {
      const prefs = await this.getPreferences();
      console.log('[Updater] Preferences:', prefs);

      if (prefs.auto_check !== false) {
        setTimeout(() => this.checkForUpdates(), 5000);

        if (prefs.auto_check && prefs.check_interval_hours) {
          const intervalMs = prefs.check_interval_hours * 60 * 60 * 1000;
          this.checkInterval = setInterval(() => {
            this.checkForUpdates();
          }, intervalMs);
          console.log(`[Updater] Periodic checking enabled (every ${prefs.check_interval_hours} hours)`);
        }
      }

      await this.getStatus();
    } catch (error) {
      console.error('[Updater] Initialization error:', error);
    }
  }

  /**
   * Get current update status
   */
  async getStatus() {
    try {
      const response = await fetch(`${BACKEND_URL}/updates/status`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const status = await response.json();
      this.updateStatus = status;
      console.log('[Updater] Status:', status);
      return status;
    } catch (error) {
      console.warn('[Updater] Error getting backend status, using fallback status:', error);
      const fallback = {
        status: 'fallback',
        current_version: FALLBACK_CURRENT_VERSION,
        channel: 'stable',
        source: 'github-release-manifest'
      };
      this.updateStatus = fallback;
      return fallback;
    }
  }

  /**
   * Check for available updates
   */
  async checkForUpdates(showNoUpdateMessage = false) {
    console.log('[Updater] Checking for updates...');

    try {
      const response = await fetch(`${BACKEND_URL}/updates/check`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('[Updater] Check result:', data);

      if (data.update_available && data.update_info) {
        this.updateStatus = data;
        this.showUpdateNotification(data.update_info);
      } else if (showNoUpdateMessage) {
        this.showNoUpdateMessage();
      }

      return data;
    } catch (error) {
      console.warn('[Updater] Backend update check failed, trying GitHub release manifest:', error);
      const fallbackData = await this.checkForUpdatesFromReleaseManifest(showNoUpdateMessage);
      if (fallbackData) {
        return fallbackData;
      }
      throw error;
    }
  }

  async checkForUpdatesFromReleaseManifest(showNoUpdateMessage = false) {
    try {
      const response = await fetch(GITHUB_RELEASE_MANIFEST_URL, {
        headers: {
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Manifest HTTP ${response.status}`);
      }

      const manifest = await response.json();
      console.log('[Updater] GitHub manifest result:', manifest);

      const latest = manifest.latest || manifest;
      const currentVersion = this.getCurrentVersion();
      const latestVersion = latest.current_version || latest.version;

      if (!latestVersion) {
        throw new Error('Release manifest missing version');
      }

      if (this.isVersionNewer(latestVersion, currentVersion)) {
        const updateInfo = this.normalizeManifestUpdateInfo(latest, currentVersion);
        const data = {
          update_available: true,
          update_info: updateInfo,
          status: 'available',
          source: 'github-release-manifest'
        };
        this.updateStatus = data;
        this.showUpdateNotification(updateInfo);
        return data;
      }

      if (showNoUpdateMessage) {
        this.showNoUpdateMessage();
      }

      return {
        update_available: false,
        update_info: null,
        status: 'up_to_date',
        source: 'github-release-manifest'
      };
    } catch (error) {
      console.error('[Updater] Error checking GitHub release manifest:', error);
      return null;
    }
  }

  normalizeManifestUpdateInfo(latest, currentVersion) {
    const releaseNotes = latest.release_notes || latest.releaseNotes || `Latest release: ${latest.version}`;
    const downloadUrl = latest.downloadUrl || latest.download_url || '';

    return {
      version: latest.version,
      current_version: currentVersion,
      release_date: latest.releaseDate || latest.release_date || latest.generated_at || new Date().toISOString(),
      size: Number(latest.size || 0),
      download_url: downloadUrl,
      sha256: latest.sha256 || '',
      critical: Boolean(latest.critical),
      requires_restart: latest.requiresRestart !== false,
      changelog: latest.changelog || {
        added: [],
        changed: [],
        fixed: []
      },
      release_notes: releaseNotes,
      release_url: latest.releaseUrl || latest.release_url || downloadUrl
    };
  }

  getCurrentVersion() {
    return this.updateStatus?.current_version || this.updateStatus?.currentVersion || FALLBACK_CURRENT_VERSION;
  }

  isVersionNewer(candidate, current) {
    const parse = (version) => String(version || '0')
      .replace(/^v/i, '')
      .split('.')
      .map((part) => Number.parseInt(part, 10) || 0);

    const a = parse(candidate);
    const b = parse(current);
    const maxLength = Math.max(a.length, b.length);

    for (let index = 0; index < maxLength; index += 1) {
      const left = a[index] || 0;
      const right = b[index] || 0;
      if (left > right) return true;
      if (left < right) return false;
    }

    return false;
  }

  /**
   * Download update
   */
  async downloadUpdate() {
    console.log('[Updater] Downloading update...');

    const updateInfo = this.updateStatus?.update_info;
    if (this.updateStatus?.source === 'github-release-manifest' && updateInfo?.download_url) {
      window.open(updateInfo.download_url, '_blank', 'noopener,noreferrer');
      this.updateDownloadProgress(100);
      this.showInstallPrompt(true);
      return {
        success: true,
        status: 'download_redirected',
        source: 'github-release-manifest',
        download_url: updateInfo.download_url
      };
    }

    try {
      const response = await fetch(`${BACKEND_URL}/updates/download`, {
        method: 'POST'
      });

      const data = await response.json();
      console.log('[Updater] Download result:', data);

      if (data.success) {
        this.updateDownloadProgress(100);
        this.showInstallPrompt();
      }

      return data;
    } catch (error) {
      console.error('[Updater] Error downloading update:', error);
      throw error;
    }
  }

  /**
   * Install update
   */
  async installUpdate() {
    console.log('[Updater] Installing update...');

    if (this.updateStatus?.source === 'github-release-manifest') {
      const releaseUrl = this.updateStatus?.update_info?.release_url || this.updateStatus?.update_info?.download_url;
      if (releaseUrl) {
        window.open(releaseUrl, '_blank', 'noopener,noreferrer');
        this.showInstallingMessage('Open the downloaded installer to complete the update.');
        return {
          success: true,
          status: 'manual_install_required',
          source: 'github-release-manifest'
        };
      }
    }

    try {
      const response = await fetch(`${BACKEND_URL}/updates/install`, {
        method: 'POST'
      });

      const data = await response.json();
      console.log('[Updater] Install result:', data);

      if (data.success) {
        this.showInstallingMessage();
      }

      return data;
    } catch (error) {
      console.error('[Updater] Error installing update:', error);
      throw error;
    }
  }

  /**
   * Get update preferences
   */
  async getPreferences() {
    try {
      const response = await fetch(`${BACKEND_URL}/updates/preferences`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('[Updater] Error getting preferences:', error);
      return {
        auto_check: true,
        auto_download: true,
        channel: 'stable',
        check_interval_hours: 6
      };
    }
  }

  /**
   * Set update preferences
   */
  async setPreferences(preferences) {
    try {
      const response = await fetch(`${BACKEND_URL}/updates/preferences`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preferences)
      });
      return await response.json();
    } catch (error) {
      console.error('[Updater] Error setting preferences:', error);
      throw error;
    }
  }

  /**
   * Show update notification
   */
  showUpdateNotification(updateInfo) {
    if (this.isNotificationVisible) return;

    console.log('[Updater] Showing update notification for version', updateInfo.version);

    const notification = document.getElementById('updateNotification');
    if (!notification) {
      console.warn('[Updater] Update notification element not found');
      return;
    }

    const versionEl = notification.querySelector('.update-version');
    const changelogEl = notification.querySelector('.update-changelog');
    const sizeEl = notification.querySelector('.update-size');

    if (versionEl) {
      versionEl.textContent = `Version ${updateInfo.version}`;
    }

    if (changelogEl) {
      if (updateInfo.changelog) {
        const changes = [];
        if (updateInfo.changelog.added && updateInfo.changelog.added.length > 0) {
          changes.push('<strong>New:</strong> ' + updateInfo.changelog.added[0]);
        }
        if (updateInfo.changelog.changed && updateInfo.changelog.changed.length > 0) {
          changes.push('<strong>Changed:</strong> ' + updateInfo.changelog.changed[0]);
        }
        if (updateInfo.changelog.fixed && updateInfo.changelog.fixed.length > 0) {
          changes.push('<strong>Fixed:</strong> ' + updateInfo.changelog.fixed[0]);
        }
        changelogEl.innerHTML = changes.length ? changes.join('<br>') : this.escapeHtml(updateInfo.release_notes || 'A new release is available.');
      } else {
        changelogEl.textContent = updateInfo.release_notes || 'A new release is available.';
      }
    }

    if (sizeEl) {
      const sizeMB = updateInfo.size ? (updateInfo.size / (1024 * 1024)).toFixed(1) : null;
      sizeEl.textContent = sizeMB ? `${sizeMB} MB` : 'Size unavailable';
    }

    notification.style.display = 'block';
    this.isNotificationVisible = true;

    const installBtn = notification.querySelector('.update-install-btn');
    const dismissBtn = notification.querySelector('.update-dismiss-btn');
    const detailsBtn = notification.querySelector('.update-details-btn');

    if (installBtn) {
      installBtn.onclick = async () => {
        installBtn.disabled = true;
        installBtn.textContent = this.updateStatus?.source === 'github-release-manifest' ? 'Open Download' : 'Downloading...';
        try {
          await this.downloadUpdate();
        } catch (error) {
          installBtn.disabled = false;
          installBtn.textContent = 'Download & Install';
          alert('Failed to download update: ' + error.message);
        }
      };
    }

    if (dismissBtn) {
      dismissBtn.onclick = () => {
        notification.style.display = 'none';
        this.isNotificationVisible = false;
      };
    }

    if (detailsBtn) {
      detailsBtn.onclick = () => {
        this.showReleaseNotes(updateInfo);
      };
    }
  }

  /**
   * Show "no update available" message
   */
  showNoUpdateMessage() {
    const statusEl = document.getElementById('updateStatus');
    if (statusEl) {
      statusEl.textContent = 'You are running the latest version';
      statusEl.className = 'update-status success';
      setTimeout(() => {
        statusEl.textContent = '';
        statusEl.className = '';
      }, 5000);
    }
  }

  /**
   * Update download progress
   */
  updateDownloadProgress(percent) {
    const progressBar = document.querySelector('.update-progress-bar');
    const progressText = document.querySelector('.update-progress-text');

    if (progressBar) {
      progressBar.style.width = `${percent}%`;
    }

    if (progressText) {
      progressText.textContent = `Downloading: ${percent.toFixed(1)}%`;
    }
  }

  /**
   * Show install prompt after download
   */
  showInstallPrompt(isManualDownload = false) {
    const notification = document.getElementById('updateNotification');
    if (!notification) return;

    const installBtn = notification.querySelector('.update-install-btn');
    if (installBtn) {
      installBtn.textContent = isManualDownload ? 'Open Release Page' : 'Install & Restart';
      installBtn.disabled = false;
      installBtn.onclick = async () => {
        if (confirm(isManualDownload
          ? 'Open the release page and run the downloaded installer?' 
          : 'Install update and restart Windows AI?')) {
          await this.installUpdate();
        }
      };
    }
  }

  /**
   * Show "installing" message
   */
  showInstallingMessage(message = 'Windows AI will restart automatically.') {
    const notification = document.getElementById('updateNotification');
    if (!notification) return;

    const content = notification.querySelector('.update-content');
    if (content) {
      content.innerHTML = `
        <h3>Installing Update...</h3>
        <p>${this.escapeHtml(message)}</p>
        <div class="spinner"></div>
      `;
    }
  }

  /**
   * Show release notes modal
   */
  showReleaseNotes(updateInfo) {
    const modal = document.createElement('div');
    modal.className = 'modal update-modal';
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-header">
          <h2>Release Notes - Version ${this.escapeHtml(updateInfo.version)}</h2>
          <button class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
          <pre>${this.escapeHtml(updateInfo.release_notes || 'No release notes available.')}</pre>
        </div>
        <div class="modal-footer">
          <button class="btn btn-primary modal-close">Close</button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    modal.querySelectorAll('.modal-close').forEach(btn => {
      btn.onclick = () => modal.remove();
    });

    modal.onclick = (e) => {
      if (e.target === modal) modal.remove();
    };
  }

  escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  /**
   * Clean up on shutdown
   */
  destroy() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
  }
}

const updateManager = new UpdateManager();

if (typeof window !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      updateManager.initialize();
    });
  } else {
    updateManager.initialize();
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = updateManager;
}
