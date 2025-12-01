/**
 * Windows AI - Auto-Update Module
 * Handles update checking, notifications, and installation
 */

const BACKEND_URL = 'http://127.0.0.1:8010';

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
      // Get update preferences
      const prefs = await this.getPreferences();
      console.log('[Updater] Preferences:', prefs);

      // Check for updates on startup
      if (prefs.auto_check !== false) {
        setTimeout(() => this.checkForUpdates(), 5000); // Check after 5 seconds

        // Set up periodic checking if enabled
        if (prefs.auto_check && prefs.check_interval_hours) {
          const intervalMs = prefs.check_interval_hours * 60 * 60 * 1000;
          this.checkInterval = setInterval(() => {
            this.checkForUpdates();
          }, intervalMs);
          console.log(`[Updater] Periodic checking enabled (every ${prefs.check_interval_hours} hours)`);
        }
      }

      // Check current update status
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
      const status = await response.json();
      this.updateStatus = status;
      console.log('[Updater] Status:', status);
      return status;
    } catch (error) {
      console.error('[Updater] Error getting status:', error);
      return null;
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
        // Update available!
        this.updateStatus = data;
        this.showUpdateNotification(data.update_info);
      } else if (showNoUpdateMessage) {
        this.showNoUpdateMessage();
      }

      return data;

    } catch (error) {
      console.error('[Updater] Error checking for updates:', error);
      throw error;
    }
  }

  /**
   * Download update
   */
  async downloadUpdate() {
    console.log('[Updater] Downloading update...');

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

    try {
      const response = await fetch(`${BACKEND_URL}/updates/install`, {
        method: 'POST'
      });

      const data = await response.json();
      console.log('[Updater] Install result:', data);

      if (data.success) {
        // Installation started, application will close
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

    // Populate notification details
    const versionEl = notification.querySelector('.update-version');
    const changelogEl = notification.querySelector('.update-changelog');
    const sizeEl = notification.querySelector('.update-size');

    if (versionEl) {
      versionEl.textContent = `Version ${updateInfo.version}`;
    }

    if (changelogEl && updateInfo.changelog) {
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
      changelogEl.innerHTML = changes.join('<br>');
    }

    if (sizeEl) {
      const sizeMB = (updateInfo.size / (1024 * 1024)).toFixed(1);
      sizeEl.textContent = `${sizeMB} MB`;
    }

    // Show notification
    notification.style.display = 'block';
    this.isNotificationVisible = true;

    // Set up event handlers
    const installBtn = notification.querySelector('.update-install-btn');
    const dismissBtn = notification.querySelector('.update-dismiss-btn');
    const detailsBtn = notification.querySelector('.update-details-btn');

    if (installBtn) {
      installBtn.onclick = async () => {
        installBtn.disabled = true;
        installBtn.textContent = 'Downloading...';
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

    if (detailsBtn && updateInfo.release_notes) {
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
  showInstallPrompt() {
    const notification = document.getElementById('updateNotification');
    if (!notification) return;

    const installBtn = notification.querySelector('.update-install-btn');
    if (installBtn) {
      installBtn.textContent = 'Install & Restart';
      installBtn.disabled = false;
      installBtn.onclick = async () => {
        if (confirm('Install update and restart Windows AI?')) {
          await this.installUpdate();
        }
      };
    }
  }

  /**
   * Show "installing" message
   */
  showInstallingMessage() {
    const notification = document.getElementById('updateNotification');
    if (!notification) return;

    const content = notification.querySelector('.update-content');
    if (content) {
      content.innerHTML = `
        <h3>Installing Update...</h3>
        <p>Windows AI will restart automatically.</p>
        <div class="spinner"></div>
      `;
    }
  }

  /**
   * Show release notes modal
   */
  showReleaseNotes(updateInfo) {
    // Create modal (or use existing modal system)
    const modal = document.createElement('div');
    modal.className = 'modal update-modal';
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-header">
          <h2>Release Notes - Version ${updateInfo.version}</h2>
          <button class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
          <pre>${updateInfo.release_notes}</pre>
        </div>
        <div class="modal-footer">
          <button class="btn btn-primary modal-close">Close</button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Close handlers
    modal.querySelectorAll('.modal-close').forEach(btn => {
      btn.onclick = () => modal.remove();
    });

    modal.onclick = (e) => {
      if (e.target === modal) modal.remove();
    };
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

// Export singleton instance
const updateManager = new UpdateManager();

// Initialize when DOM is ready
if (typeof window !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      updateManager.initialize();
    });
  } else {
    updateManager.initialize();
  }
}

// Export for Node.js if available (not used in browser context)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = updateManager;
}
