/**
 * Windows-AI Actions API - Sync Integration
 *
 * Provides API endpoints for controlling cloud sync from the GUI and other clients.
 */

import { Router, Request, Response } from 'express';

const router = Router();

// Types
interface SyncStatusResponse {
  device_id: string;
  device_name: string;
  background_sync_enabled: boolean;
  categories: Record<string, any>;
  devices: any[];
  pending_changes: Record<string, number>;
}

interface DeviceInfo {
  device_id: string;
  device_name: string;
  platform: string;
  os_version: string;
  app_version: string;
  last_seen: string;
  is_active: boolean;
  sync_priority: number;
}

interface SyncResult {
  success: boolean;
  pushed?: number;
  pulled?: number;
  conflicts?: number;
  error?: string;
}

// Mock sync client for now - in production, this would connect to Python backend
class SyncAPIClient {
  private backendUrl: string;

  constructor(backendUrl: string = 'http://localhost:8000') {
    this.backendUrl = backendUrl;
  }

  async request(method: string, endpoint: string, data?: any): Promise<any> {
    const url = `${this.backendUrl}${endpoint}`;
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Sync API request failed: ${error}`);
      throw error;
    }
  }

  async getStatus(): Promise<SyncStatusResponse> {
    return await this.request('GET', '/api/sync/status');
  }

  async startBackgroundSync(): Promise<{ success: boolean }> {
    return await this.request('POST', '/api/sync/start');
  }

  async stopBackgroundSync(): Promise<{ success: boolean }> {
    return await this.request('POST', '/api/sync/stop');
  }

  async syncNow(category?: string): Promise<SyncResult> {
    const endpoint = category
      ? `/api/sync/now/${category}`
      : '/api/sync/now';
    return await this.request('POST', endpoint);
  }

  async pushNow(category: string): Promise<SyncResult> {
    return await this.request('POST', `/api/sync/push/${category}`);
  }

  async pullNow(category: string): Promise<SyncResult> {
    return await this.request('POST', `/api/sync/pull/${category}`);
  }

  async getDevices(): Promise<DeviceInfo[]> {
    const response = await this.request('GET', '/api/sync/devices');
    return response.devices || [];
  }

  async getConflicts(category?: string): Promise<any[]> {
    const endpoint = category
      ? `/api/sync/conflicts?category=${category}`
      : '/api/sync/conflicts';
    const response = await this.request('GET', endpoint);
    return response.conflicts || [];
  }

  async resolveConflict(conflictId: string, resolution: string): Promise<{ success: boolean }> {
    return await this.request('POST', '/api/sync/conflicts/resolve', {
      conflict_id: conflictId,
      resolution,
    });
  }

  async setSelectiveSync(categories: string[]): Promise<{ success: boolean }> {
    return await this.request('POST', '/api/sync/selective', { categories });
  }

  async getEncryptionKeyBackup(backupPassword: string): Promise<{ backup: string }> {
    return await this.request('POST', '/api/sync/encryption/backup', {
      backup_password: backupPassword,
    });
  }

  async restoreEncryptionKey(backup: string, backupPassword: string): Promise<{ success: boolean }> {
    return await this.request('POST', '/api/sync/encryption/restore', {
      backup,
      backup_password: backupPassword,
    });
  }

  async pingServer(): Promise<{ status: string }> {
    return await this.request('GET', '/api/sync/ping');
  }
}

const syncClient = new SyncAPIClient();

// ========== Sync Control Endpoints ==========

/**
 * GET /sync/status
 * Get overall sync status
 */
router.get('/status', async (req: Request, res: Response) => {
  try {
    const status = await syncClient.getStatus();
    res.json(status);
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get sync status',
      message: error instanceof Error ? error.message : String(error),
    });
  }
});

/**
 * POST /sync/start
 * Start background sync
 */
router.post('/start', async (req: Request, res: Response) => {
  try {
    const result = await syncClient.startBackgroundSync();
    res.json(result);
  } catch (error) {
    res.status(500).json({
      error: 'Failed to start background sync',
      message: error instanceof Error ? error.message : String(error),
    });
  }
});

/**
 * POST /sync/stop
 * Stop background sync
 */
router.post('/stop', async (req: Request, res: Response) => {
  try {
    const result = await syncClient.stopBackgroundSync();
    res.json(result);
  } catch (error) {
    res.status(500).json({
      error: 'Failed to stop background sync',
      message: error instanceof Error ? error.message : String(error),
    });
  }
});

/**
 * POST /sync/now
 * Trigger immediate sync for all categories
 */
router.post('/now', async (req: Request, res: Response) => {
  try {
    const result = await syncClient.syncNow();
    res.json(result);
  } catch (error) {
    res.status(500).json({
      error: 'Failed to sync now',
      message: error instanceof Error ? error.message : String(error),
    });
  }
});

/**
 * POST /sync/now/:category
 * Trigger immediate sync for specific category
 */
router.post('/now/:category', async (req: Request, res: Response) => {
  try {
    const { category } = req.params;
    const result = await syncClient.syncNow(category);
    res.json(result);
  } catch (error) {
    res.status(500).json({
      error: `Failed to sync ${req.params.category}`,
      message: error instanceof Error ? error.message : String(error),
    });
  }
});

/**
 * POST /sync/push/:category
 * Push local changes for a category
 */
router.post('/push/:category', async (req: Request, res: Response) => {
  try {
    const { category } = req.params;
    const result = await syncClient.pushNow(category);
    res.json(result);
  } catch (error) {
    res.status(500).json({
      error: `Failed to push ${req.params.category}`,
      message: error instanceof Error ? error.message : String(error),
    });
  }
});

/**
 * POST /sync/pull/:category
 * Pull remote changes for a category
 */
router.post('/pull/:category', async (req: Request, res: Response) => {
  try {
    const { category } = req.params;
    const result = await syncClient.pullNow(category);
    res.json(result);
  } catch (error) {
    res.status(500).json({
      error: `Failed to pull ${req.params.category}`,
      message: error instanceof Error ? error.message : String(error),
    });
  }
});

// ========== Device Management ==========

/**
 * GET /sync/devices
 * List all synced devices
 */
router.get('/devices', async (req: Request, res: Response) => {
  try {
    const devices = await syncClient.getDevices();
    res.json({ devices });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get devices',
      message: error instanceof Error ? error.message : String(error),
    });
  }
});

// ========== Conflict Resolution ==========

/**
 * GET /sync/conflicts
 * Get unresolved conflicts
 */
router.get('/conflicts', async (req: Request, res: Response) => {
  try {
    const { category } = req.query;
    const conflicts = await syncClient.getConflicts(category as string);
    res.json({ conflicts });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get conflicts',
      message: error instanceof Error ? error.message : String(error),
    });
  }
});

/**
 * POST /sync/conflicts/resolve
 * Resolve a conflict
 */
router.post('/conflicts/resolve', async (req: Request, res: Response) => {
  try {
    const { conflict_id, resolution } = req.body;

    if (!conflict_id || !resolution) {
      return res.status(400).json({
        error: 'Missing required fields: conflict_id, resolution',
      });
    }

    const result = await syncClient.resolveConflict(conflict_id, resolution);
    res.json(result);
  } catch (error) {
    res.status(500).json({
      error: 'Failed to resolve conflict',
      message: error instanceof Error ? error.message : String(error),
    });
  }
});

// ========== Configuration ==========

/**
 * POST /sync/selective
 * Configure selective sync
 */
router.post('/selective', async (req: Request, res: Response) => {
  try {
    const { categories } = req.body;

    if (!Array.isArray(categories)) {
      return res.status(400).json({
        error: 'categories must be an array',
      });
    }

    const result = await syncClient.setSelectiveSync(categories);
    res.json(result);
  } catch (error) {
    res.status(500).json({
      error: 'Failed to set selective sync',
      message: error instanceof Error ? error.message : String(error),
    });
  }
});

// ========== Encryption Key Management ==========

/**
 * POST /sync/encryption/backup
 * Create encrypted backup of encryption key
 */
router.post('/encryption/backup', async (req: Request, res: Response) => {
  try {
    const { backup_password } = req.body;

    if (!backup_password) {
      return res.status(400).json({
        error: 'backup_password required',
      });
    }

    const result = await syncClient.getEncryptionKeyBackup(backup_password);
    res.json(result);
  } catch (error) {
    res.status(500).json({
      error: 'Failed to create key backup',
      message: error instanceof Error ? error.message : String(error),
    });
  }
});

/**
 * POST /sync/encryption/restore
 * Restore encryption key from backup
 */
router.post('/encryption/restore', async (req: Request, res: Response) => {
  try {
    const { backup, backup_password } = req.body;

    if (!backup || !backup_password) {
      return res.status(400).json({
        error: 'backup and backup_password required',
      });
    }

    const result = await syncClient.restoreEncryptionKey(backup, backup_password);
    res.json(result);
  } catch (error) {
    res.status(500).json({
      error: 'Failed to restore key',
      message: error instanceof Error ? error.message : String(error),
    });
  }
});

// ========== Server Status ==========

/**
 * GET /sync/ping
 * Ping sync server
 */
router.get('/ping', async (req: Request, res: Response) => {
  try {
    const result = await syncClient.pingServer();
    res.json(result);
  } catch (error) {
    res.status(500).json({
      error: 'Sync server unreachable',
      message: error instanceof Error ? error.message : String(error),
    });
  }
});

export default router;
