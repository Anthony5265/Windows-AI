/**
 * Actions API - Secure System Integration for Windows-AI
 * Main server with comprehensive security, audit logging, and system operations
 */

import express, { Request, Response, NextFunction } from 'express';
import { fileURLToPath } from 'node:url';
import {
  authenticate,
  optionalAuth,
  authorize,
  rateLimit,
  bodySizeLimit,
  corsWithWhitelist,
  JWTAuth,
} from './middleware/security.js';
import { auditLog, auditLogger } from './middleware/audit.js';
import { ApiException, normalizeError } from './errors.js';
import { CommandExecutor } from './services/command-executor.js';
import { FileOperations } from './services/file-operations.js';
import { SystemOperations } from './services/system-operations.js';
import { Permission, ApiResponse } from './types/index.js';

// =====================================================================
// Express Application Setup
// =====================================================================

export const app = express();

// =====================================================================
// Global Middleware
// =====================================================================

// CORS
app.use(corsWithWhitelist([
  'http://localhost:8010',
  'http://127.0.0.1:8010',
  'http://localhost:3000',
  'http://127.0.0.1:3000',
]));

// Body parsing with size limits
app.use(express.json({ limit: '10mb' }));
app.use(bodySizeLimit(10 * 1024 * 1024)); // 10MB

// Audit logging
app.use(auditLog);

// Rate limiting (global)
app.use(rateLimit());

// =====================================================================
// Health Check & Status
// =====================================================================

/**
 * Health check endpoint (no auth required)
 */
app.get('/health', (req: Request, res: Response) => {
  res.json({
    ok: true,
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
  });
});

/**
 * API status with detailed info (auth required)
 */
app.get('/status', authenticate, async (req: Request, res: Response) => {
  try {
    const systemInfo = await SystemOperations.getSystemInfo();
    res.json({
      ok: true,
      result: {
        api: {
          version: '1.0.0',
          uptime: process.uptime(),
        },
        system: systemInfo,
      },
    });
  } catch (error) {
    const apiError = normalizeError(error);
    res.status(apiError.statusCode).json({
      ok: false,
      error: apiError.toJSON(),
    });
  }
});

// =====================================================================
// Authentication
// =====================================================================

/**
 * Generate JWT token (for internal services)
 */
app.post('/auth/token', (req: Request, res: Response) => {
  try {
    const { serviceId, permissions } = req.body;

    if (!serviceId) {
      throw new ApiException(
        'VALIDATION_ERROR' as any,
        'serviceId is required',
        400
      );
    }

    const token = JWTAuth.sign({
      sub: serviceId,
      iat: Math.floor(Date.now() / 1000),
      exp: 0, // Will be set by sign()
      permissions: permissions || [Permission.ADMIN], // Default to admin for internal services
    });

    res.json({
      ok: true,
      result: { token },
    });
  } catch (error) {
    const apiError = normalizeError(error);
    res.status(apiError.statusCode).json({
      ok: false,
      error: apiError.toJSON(),
    });
  }
});

// =====================================================================
// File Operations Endpoints
// =====================================================================

/**
 * Read file
 */
app.post(
  '/api/files/read',
  authenticate,
  authorize(Permission.FILE_READ),
  async (req: Request, res: Response) => {
    try {
      const user = (req as any).user;
      const result = await FileOperations.readFile(req.body, user?.sub);
      res.json({ ok: true, result });
    } catch (error) {
      const apiError = normalizeError(error);
      res.status(apiError.statusCode).json({
        ok: false,
        error: apiError.toJSON(),
      });
    }
  }
);

/**
 * Write file
 */
app.post(
  '/api/files/write',
  authenticate,
  authorize(Permission.FILE_WRITE),
  async (req: Request, res: Response) => {
    try {
      const user = (req as any).user;
      const result = await FileOperations.writeFile(req.body, user?.sub);
      res.json({ ok: true, result });
    } catch (error) {
      const apiError = normalizeError(error);
      res.status(apiError.statusCode).json({
        ok: false,
        error: apiError.toJSON(),
      });
    }
  }
);

/**
 * Copy file
 */
app.post(
  '/api/files/copy',
  authenticate,
  authorize(Permission.FILE_WRITE),
  async (req: Request, res: Response) => {
    try {
      const user = (req as any).user;
      const result = await FileOperations.copyFile(req.body, user?.sub);
      res.json({ ok: true, result });
    } catch (error) {
      const apiError = normalizeError(error);
      res.status(apiError.statusCode).json({
        ok: false,
        error: apiError.toJSON(),
      });
    }
  }
);

/**
 * Move file
 */
app.post(
  '/api/files/move',
  authenticate,
  authorize(Permission.FILE_WRITE),
  async (req: Request, res: Response) => {
    try {
      const user = (req as any).user;
      const result = await FileOperations.moveFile(req.body, user?.sub);
      res.json({ ok: true, result });
    } catch (error) {
      const apiError = normalizeError(error);
      res.status(apiError.statusCode).json({
        ok: false,
        error: apiError.toJSON(),
      });
    }
  }
);

/**
 * Delete file
 */
app.post(
  '/api/files/delete',
  authenticate,
  authorize(Permission.FILE_DELETE),
  async (req: Request, res: Response) => {
    try {
      const user = (req as any).user;
      const result = await FileOperations.deleteFile(req.body, user?.sub);
      res.json({ ok: true, result });
    } catch (error) {
      const apiError = normalizeError(error);
      res.status(apiError.statusCode).json({
        ok: false,
        error: apiError.toJSON(),
      });
    }
  }
);

/**
 * List directory
 */
app.post(
  '/api/files/list',
  authenticate,
  authorize(Permission.FILE_READ),
  async (req: Request, res: Response) => {
    try {
      const user = (req as any).user;
      const result = await FileOperations.listDirectory(req.body, user?.sub);
      res.json({ ok: true, result });
    } catch (error) {
      const apiError = normalizeError(error);
      res.status(apiError.statusCode).json({
        ok: false,
        error: apiError.toJSON(),
      });
    }
  }
);

// =====================================================================
// Command Execution Endpoints
// =====================================================================

/**
 * Execute command
 */
app.post(
  '/api/commands/execute',
  authenticate,
  authorize(Permission.FILE_EXECUTE),
  async (req: Request, res: Response) => {
    try {
      const user = (req as any).user;
      const result = await CommandExecutor.execute(req.body, user?.sub);
      res.json({ ok: true, result });
    } catch (error) {
      const apiError = normalizeError(error);
      res.status(apiError.statusCode).json({
        ok: false,
        error: apiError.toJSON(),
      });
    }
  }
);

/**
 * Execute shell command (admin only)
 */
app.post(
  '/api/commands/shell',
  authenticate,
  authorize(Permission.ADMIN),
  async (req: Request, res: Response) => {
    try {
      const user = (req as any).user;
      const { command, options } = req.body;
      const result = await CommandExecutor.executeShell(command, options, user?.sub);
      res.json({ ok: true, result });
    } catch (error) {
      const apiError = normalizeError(error);
      res.status(apiError.statusCode).json({
        ok: false,
        error: apiError.toJSON(),
      });
    }
  }
);

// =====================================================================
// System Information Endpoints
// =====================================================================

/**
 * Get system information
 */
app.get(
  '/api/system/info',
  authenticate,
  authorize(Permission.SYSTEM_INFO),
  async (req: Request, res: Response) => {
    try {
      const user = (req as any).user;
      const result = await SystemOperations.getSystemInfo(user?.sub);
      res.json({ ok: true, result });
    } catch (error) {
      const apiError = normalizeError(error);
      res.status(apiError.statusCode).json({
        ok: false,
        error: apiError.toJSON(),
      });
    }
  }
);

/**
 * Show system notification
 */
app.post(
  '/api/system/notification',
  authenticate,
  authorize(Permission.SYSTEM_MODIFY),
  async (req: Request, res: Response) => {
    try {
      const user = (req as any).user;
      const result = await SystemOperations.showNotification(req.body, user?.sub);
      res.json({ ok: true, result });
    } catch (error) {
      const apiError = normalizeError(error);
      res.status(apiError.statusCode).json({
        ok: false,
        error: apiError.toJSON(),
      });
    }
  }
);

// =====================================================================
// Process Management Endpoints
// =====================================================================

/**
 * List processes
 */
app.get(
  '/api/processes/list',
  authenticate,
  authorize(Permission.PROCESS_LIST),
  async (req: Request, res: Response) => {
    try {
      const user = (req as any).user;
      const result = await SystemOperations.listProcesses(user?.sub);
      res.json({ ok: true, result });
    } catch (error) {
      const apiError = normalizeError(error);
      res.status(apiError.statusCode).json({
        ok: false,
        error: apiError.toJSON(),
      });
    }
  }
);

/**
 * Start process
 */
app.post(
  '/api/processes/start',
  authenticate,
  authorize(Permission.PROCESS_START),
  async (req: Request, res: Response) => {
    try {
      const user = (req as any).user;
      const result = await SystemOperations.startProcess(req.body, user?.sub);
      res.json({ ok: true, result });
    } catch (error) {
      const apiError = normalizeError(error);
      res.status(apiError.statusCode).json({
        ok: false,
        error: apiError.toJSON(),
      });
    }
  }
);

/**
 * Kill process
 */
app.post(
  '/api/processes/kill',
  authenticate,
  authorize(Permission.PROCESS_KILL),
  async (req: Request, res: Response) => {
    try {
      const user = (req as any).user;
      const result = await SystemOperations.killProcess(req.body, user?.sub);
      res.json({ ok: true, result });
    } catch (error) {
      const apiError = normalizeError(error);
      res.status(apiError.statusCode).json({
        ok: false,
        error: apiError.toJSON(),
      });
    }
  }
);

// =====================================================================
// Legacy Routes (for backward compatibility)
// =====================================================================

import { executeAction } from './actions.js';
import { normalize } from './normalize.js';
import { createPairingToken, handleRemoteCommand } from './mobile.js';
import { distributeTask } from './mesh.js';
import { handleDeviceEvent } from './iot.js';
import { searchDocuments } from './search.js';

app.post('/api/actions/execute', optionalAuth, async (req, res) => {
  try {
    const norm = normalize(req.body);
    const result = await executeAction(norm);
    res.json({ ok: true, result });
  } catch (error) {
    const apiError = normalizeError(error);
    res.status(apiError.statusCode).json({
      ok: false,
      error: apiError.toJSON(),
    });
  }
});

app.post('/api/mobile/pair', optionalAuth, (req, res) => {
  try {
    const token = createPairingToken(req.body.deviceId);
    res.json({ ok: true, token });
  } catch (error) {
    const apiError = normalizeError(error);
    res.status(apiError.statusCode).json({
      ok: false,
      error: apiError.toJSON(),
    });
  }
});

app.post('/api/mobile/command', optionalAuth, async (req, res) => {
  try {
    const { token, ...body } = req.body;
    const result = await handleRemoteCommand(token, body);
    res.json({ ok: true, result });
  } catch (error) {
    const apiError = normalizeError(error);
    res.status(apiError.statusCode).json({
      ok: false,
      error: apiError.toJSON(),
    });
  }
});

app.post('/api/mesh/distribute', optionalAuth, (req, res) => {
  try {
    const result = distributeTask(req.body);
    res.json({ ok: true, result });
  } catch (error) {
    const apiError = normalizeError(error);
    res.status(apiError.statusCode).json({
      ok: false,
      error: apiError.toJSON(),
    });
  }
});

app.post('/api/iot/event', optionalAuth, (req, res) => {
  try {
    const result = handleDeviceEvent(req.body);
    res.json({ ok: true, result });
  } catch (error) {
    const apiError = normalizeError(error);
    res.status(apiError.statusCode).json({
      ok: false,
      error: apiError.toJSON(),
    });
  }
});

app.post('/api/search/query', optionalAuth, (req, res) => {
  try {
    const result = searchDocuments(req.body);
    res.json({ ok: true, result });
  } catch (error) {
    const apiError = normalizeError(error);
    res.status(apiError.statusCode).json({
      ok: false,
      error: apiError.toJSON(),
    });
  }
});

// =====================================================================
// Error Handler
// =====================================================================

app.use((error: any, req: Request, res: Response, next: NextFunction) => {
  const apiError = normalizeError(error);
  res.status(apiError.statusCode).json({
    ok: false,
    error: apiError.toJSON(),
    timestamp: new Date().toISOString(),
  });
});

// =====================================================================
// Server Startup
// =====================================================================

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const port = parseInt(process.env.PORT || '3000', 10);
  const host = process.env.HOST || '127.0.0.1';

  const server = app.listen(port, host, () => {
    console.log(
      JSON.stringify({
        level: 'info',
        message: 'Actions API listening',
        port,
        host,
        timestamp: new Date().toISOString(),
      })
    );
  });

  // Graceful shutdown
  process.on('SIGTERM', async () => {
    console.log('SIGTERM received, shutting down gracefully...');
    server.close(() => {
      console.log('Server closed');
    });
    await auditLogger.close();
    process.exit(0);
  });

  process.on('SIGINT', async () => {
    console.log('SIGINT received, shutting down gracefully...');
    server.close(() => {
      console.log('Server closed');
    });
    await auditLogger.close();
    process.exit(0);
  });
}
