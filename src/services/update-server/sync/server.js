/**
 * Windows-AI Cloud Sync Server
 *
 * Express.js server for handling cloud synchronization requests
 * with JWT authentication, device management, and storage backends.
 */

const express = require('express');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const sqlite3 = require('sqlite3').verbose();
const { promisify } = require('util');
const crypto = require('crypto');
const path = require('path');
const fs = require('fs').promises;

const app = express();
const PORT = process.env.SYNC_PORT || 8765;
const JWT_SECRET = process.env.JWT_SECRET || crypto.randomBytes(32).toString('hex');
const DB_PATH = process.env.SYNC_DB_PATH || path.join(__dirname, 'sync_server.db');

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Logging middleware
app.use((req, res, next) => {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] ${req.method} ${req.path}`);
    next();
});

// ========== Database Setup ==========

class SyncDatabase {
    constructor(dbPath) {
        this.db = new sqlite3.Database(dbPath);
        this.run = promisify(this.db.run.bind(this.db));
        this.get = promisify(this.db.get.bind(this.db));
        this.all = promisify(this.db.all.bind(this.db));
        this.initDatabase();
    }

    async initDatabase() {
        await this.run(`
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                quota_bytes INTEGER DEFAULT 10737418240,
                used_bytes INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            )
        `);

        await this.run(`
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                device_name TEXT NOT NULL,
                platform TEXT NOT NULL,
                os_version TEXT NOT NULL,
                app_version TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                sync_priority INTEGER DEFAULT 100,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        `);

        await this.run(`
            CREATE TABLE IF NOT EXISTS sync_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                category TEXT NOT NULL,
                item_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                data TEXT,
                version INTEGER DEFAULT 1,
                timestamp TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (device_id) REFERENCES devices(device_id),
                UNIQUE(user_id, category, item_id)
            )
        `);

        await this.run(`
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                category TEXT NOT NULL,
                operation TEXT NOT NULL,
                item_count INTEGER DEFAULT 1,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (device_id) REFERENCES devices(device_id)
            )
        `);

        await this.run(`
            CREATE TABLE IF NOT EXISTS conflicts (
                conflict_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                item_id TEXT NOT NULL,
                device1_id TEXT NOT NULL,
                device2_id TEXT NOT NULL,
                device1_version INTEGER NOT NULL,
                device2_version INTEGER NOT NULL,
                resolution TEXT,
                resolved INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        `);

        // Create indexes
        await this.run('CREATE INDEX IF NOT EXISTS idx_sync_data_user ON sync_data(user_id, category, timestamp)');
        await this.run('CREATE INDEX IF NOT EXISTS idx_sync_history_user ON sync_history(user_id, timestamp)');
        await this.run('CREATE INDEX IF NOT EXISTS idx_devices_user ON devices(user_id, is_active)');
        await this.run('CREATE INDEX IF NOT EXISTS idx_conflicts_user ON conflicts(user_id, resolved)');

        console.log('Database initialized');
    }

    // User management
    async createUser(username, passwordHash, email = null) {
        const userId = crypto.randomBytes(16).toString('hex');
        await this.run(
            'INSERT INTO users (user_id, username, password_hash, email) VALUES (?, ?, ?, ?)',
            [userId, username, passwordHash, email]
        );
        return userId;
    }

    async getUser(username) {
        return await this.get('SELECT * FROM users WHERE username = ?', [username]);
    }

    async getUserById(userId) {
        return await this.get('SELECT * FROM users WHERE user_id = ?', [userId]);
    }

    async updateUserQuota(userId, usedBytes) {
        await this.run(
            'UPDATE users SET used_bytes = ? WHERE user_id = ?',
            [usedBytes, userId]
        );
    }

    // Device management
    async registerDevice(userId, deviceInfo) {
        await this.run(`
            INSERT OR REPLACE INTO devices
            (device_id, user_id, device_name, platform, os_version, app_version, last_seen, is_active, sync_priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        `, [
            deviceInfo.device_id,
            userId,
            deviceInfo.device_name,
            deviceInfo.platform,
            deviceInfo.os_version,
            deviceInfo.app_version,
            deviceInfo.last_seen,
            deviceInfo.is_active ? 1 : 0,
            deviceInfo.sync_priority || 100
        ]);
    }

    async getDevices(userId, activeOnly = true) {
        const query = activeOnly
            ? 'SELECT * FROM devices WHERE user_id = ? AND is_active = 1 ORDER BY sync_priority, last_seen DESC'
            : 'SELECT * FROM devices WHERE user_id = ? ORDER BY sync_priority, last_seen DESC';
        return await this.all(query, [userId]);
    }

    async updateDeviceStatus(deviceId, isActive, lastSeen) {
        await this.run(
            'UPDATE devices SET is_active = ?, last_seen = ? WHERE device_id = ?',
            [isActive ? 1 : 0, lastSeen, deviceId]
        );
    }

    // Sync data management
    async saveChanges(userId, deviceId, category, changes) {
        for (const change of changes) {
            await this.run(`
                INSERT OR REPLACE INTO sync_data
                (user_id, device_id, category, item_id, operation, data, version, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            `, [
                userId,
                deviceId,
                category,
                change.item_id,
                change.operation,
                change.data,
                change.version,
                change.timestamp
            ]);
        }
    }

    async getChanges(userId, category, since = null, limit = 100) {
        let query = `
            SELECT * FROM sync_data
            WHERE user_id = ? AND category = ?
        `;
        const params = [userId, category];

        if (since) {
            query += ' AND timestamp > ?';
            params.push(since);
        }

        query += ' ORDER BY timestamp ASC LIMIT ?';
        params.push(limit);

        return await this.all(query, params);
    }

    // Sync history
    async recordSyncHistory(userId, deviceId, category, operation, itemCount) {
        await this.run(`
            INSERT INTO sync_history (user_id, device_id, category, operation, item_count)
            VALUES (?, ?, ?, ?, ?)
        `, [userId, deviceId, category, operation, itemCount]);
    }

    async getSyncHistory(userId, limit = 50) {
        return await this.all(
            'SELECT * FROM sync_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?',
            [userId, limit]
        );
    }

    // Conflict management
    async recordConflict(userId, category, itemId, device1Id, device2Id, version1, version2) {
        const conflictId = crypto.randomBytes(16).toString('hex');
        await this.run(`
            INSERT INTO conflicts
            (conflict_id, user_id, category, item_id, device1_id, device2_id, device1_version, device2_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        `, [conflictId, userId, category, itemId, device1Id, device2Id, version1, version2]);
        return conflictId;
    }

    async getConflicts(userId, resolvedOnly = false) {
        const query = resolvedOnly
            ? 'SELECT * FROM conflicts WHERE user_id = ? AND resolved = 0 ORDER BY created_at DESC'
            : 'SELECT * FROM conflicts WHERE user_id = ? ORDER BY created_at DESC';
        return await this.all(query, [userId]);
    }

    async resolveConflict(conflictId, resolution) {
        await this.run(
            'UPDATE conflicts SET resolved = 1, resolution = ? WHERE conflict_id = ?',
            [resolution, conflictId]
        );
    }
}

const db = new SyncDatabase(DB_PATH);

// ========== Authentication Middleware ==========

function hashPassword(password) {
    return crypto.createHash('sha256').update(password).digest('hex');
}

function generateToken(userId, deviceId) {
    return jwt.sign({ userId, deviceId }, JWT_SECRET, { expiresIn: '30d' });
}

function verifyToken(token) {
    try {
        return jwt.verify(token, JWT_SECRET);
    } catch (err) {
        return null;
    }
}

async function authMiddleware(req, res, next) {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'Missing or invalid authorization header' });
    }

    const token = authHeader.substring(7);
    const decoded = verifyToken(token);

    if (!decoded) {
        return res.status(401).json({ error: 'Invalid or expired token' });
    }

    // Attach user info to request
    req.userId = decoded.userId;
    req.deviceId = decoded.deviceId;

    next();
}

// ========== API Routes ==========

// Health check
app.get('/api/sync/v1/ping', (req, res) => {
    res.json({
        status: 'ok',
        version: '1.0',
        timestamp: new Date().toISOString()
    });
});

// Server info
app.get('/api/sync/v1/info', (req, res) => {
    res.json({
        version: '1.0',
        protocol_version: '1.0',
        capabilities: [
            'device_management',
            'conflict_resolution',
            'selective_sync',
            'compression',
            'e2e_encryption'
        ],
        max_upload_size: 52428800, // 50MB
        supported_categories: [
            'conversations',
            'settings',
            'automations',
            'workflows',
            'documents',
            'plugins',
            'models'
        ]
    });
});

// User registration
app.post('/api/sync/v1/auth/register', async (req, res) => {
    try {
        const { username, password, email } = req.body;

        if (!username || !password) {
            return res.status(400).json({ error: 'Username and password required' });
        }

        // Check if user exists
        const existing = await db.getUser(username);
        if (existing) {
            return res.status(409).json({ error: 'Username already exists' });
        }

        // Create user
        const passwordHash = hashPassword(password);
        const userId = await db.createUser(username, passwordHash, email);

        res.json({
            success: true,
            user_id: userId,
            message: 'User registered successfully'
        });
    } catch (err) {
        console.error('Registration error:', err);
        res.status(500).json({ error: 'Registration failed' });
    }
});

// User login
app.post('/api/sync/v1/auth/login', async (req, res) => {
    try {
        const { username, password, device_id } = req.body;

        if (!username || !password) {
            return res.status(400).json({ error: 'Username and password required' });
        }

        // Get user
        const user = await db.getUser(username);
        if (!user) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        // Verify password
        const passwordHash = hashPassword(password);
        if (passwordHash !== user.password_hash) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        // Generate token
        const token = generateToken(user.user_id, device_id || 'web');

        // Update last login
        await db.run(
            'UPDATE users SET last_login = ? WHERE user_id = ?',
            [new Date().toISOString(), user.user_id]
        );

        res.json({
            success: true,
            auth_token: token,
            user_id: user.user_id,
            quota_bytes: user.quota_bytes,
            used_bytes: user.used_bytes
        });
    } catch (err) {
        console.error('Login error:', err);
        res.status(500).json({ error: 'Login failed' });
    }
});

// Device registration
app.post('/api/sync/v1/devices/register', authMiddleware, async (req, res) => {
    try {
        const deviceInfo = req.body;
        await db.registerDevice(req.userId, deviceInfo);

        res.json({
            success: true,
            device_id: deviceInfo.device_id,
            message: 'Device registered successfully'
        });
    } catch (err) {
        console.error('Device registration error:', err);
        res.status(500).json({ error: 'Device registration failed' });
    }
});

// List devices
app.get('/api/sync/v1/devices', authMiddleware, async (req, res) => {
    try {
        const devices = await db.getDevices(req.userId);
        res.json({ devices });
    } catch (err) {
        console.error('List devices error:', err);
        res.status(500).json({ error: 'Failed to list devices' });
    }
});

// Update device status
app.put('/api/sync/v1/devices/:deviceId/status', authMiddleware, async (req, res) => {
    try {
        const { deviceId } = req.params;
        const { is_active, last_seen } = req.body;

        await db.updateDeviceStatus(deviceId, is_active, last_seen);

        res.json({ success: true });
    } catch (err) {
        console.error('Update device status error:', err);
        res.status(500).json({ error: 'Failed to update device status' });
    }
});

// Pull changes
app.get('/api/sync/v1/pull', authMiddleware, async (req, res) => {
    try {
        const { category, since, limit = 100 } = req.query;

        if (!category) {
            return res.status(400).json({ error: 'Category required' });
        }

        const changes = await db.getChanges(req.userId, category, since, parseInt(limit));

        await db.recordSyncHistory(req.userId, req.deviceId, category, 'pull', changes.length);

        res.json({ changes });
    } catch (err) {
        console.error('Pull changes error:', err);
        res.status(500).json({ error: 'Failed to pull changes' });
    }
});

// Push changes
app.post('/api/sync/v1/push', authMiddleware, async (req, res) => {
    try {
        const { category, changes, device_id } = req.body;

        if (!category || !changes || !Array.isArray(changes)) {
            return res.status(400).json({ error: 'Invalid request body' });
        }

        await db.saveChanges(req.userId, device_id || req.deviceId, category, changes);
        await db.recordSyncHistory(req.userId, req.deviceId, category, 'push', changes.length);

        res.json({
            success: true,
            synced: changes.length,
            timestamp: new Date().toISOString()
        });
    } catch (err) {
        console.error('Push changes error:', err);
        res.status(500).json({ error: 'Failed to push changes' });
    }
});

// Resolve conflict
app.post('/api/sync/v1/conflicts/resolve', authMiddleware, async (req, res) => {
    try {
        const { conflict_id, resolution } = req.body;

        if (!conflict_id || !resolution) {
            return res.status(400).json({ error: 'conflict_id and resolution required' });
        }

        await db.resolveConflict(conflict_id, resolution);

        res.json({ success: true });
    } catch (err) {
        console.error('Resolve conflict error:', err);
        res.status(500).json({ error: 'Failed to resolve conflict' });
    }
});

// Get sync history
app.get('/api/sync/v1/history', authMiddleware, async (req, res) => {
    try {
        const { limit = 50 } = req.query;
        const history = await db.getSyncHistory(req.userId, parseInt(limit));
        res.json({ history });
    } catch (err) {
        console.error('Get history error:', err);
        res.status(500).json({ error: 'Failed to get sync history' });
    }
});

// ========== Error Handling ==========

app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({
        error: 'Internal server error',
        message: err.message
    });
});

// ========== Start Server ==========

app.listen(PORT, () => {
    console.log(`
╔════════════════════════════════════════════════════════╗
║     Windows-AI Cloud Sync Server                       ║
║     Version 1.0                                         ║
╚════════════════════════════════════════════════════════╝

Server running on: http://localhost:${PORT}
Database: ${DB_PATH}
JWT Secret: ${JWT_SECRET.substring(0, 10)}...

API Endpoints:
  POST /api/sync/v1/auth/register
  POST /api/sync/v1/auth/login
  POST /api/sync/v1/devices/register
  GET  /api/sync/v1/devices
  GET  /api/sync/v1/pull
  POST /api/sync/v1/push
  GET  /api/sync/v1/history
  POST /api/sync/v1/conflicts/resolve
  GET  /api/sync/v1/ping
  GET  /api/sync/v1/info
    `);
});

module.exports = app;
