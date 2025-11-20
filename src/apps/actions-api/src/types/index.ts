/**
 * Comprehensive TypeScript Type Definitions for Actions API
 * Provides type safety for all requests, responses, and internal operations
 */

// =====================================================================
// Base Types
// =====================================================================

/**
 * Standard API response wrapper
 */
export interface ApiResponse<T = any> {
  ok: boolean;
  result?: T;
  error?: ApiError;
  timestamp?: string;
}

/**
 * Structured error response
 */
export interface ApiError {
  code: ErrorCode;
  message: string;
  details?: Record<string, any>;
  suggestions?: string[];
}

/**
 * Error classification codes
 */
export enum ErrorCode {
  // Validation Errors (400)
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  INVALID_INPUT = 'INVALID_INPUT',
  MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD',

  // Authentication Errors (401)
  UNAUTHORIZED = 'UNAUTHORIZED',
  INVALID_TOKEN = 'INVALID_TOKEN',
  TOKEN_EXPIRED = 'TOKEN_EXPIRED',

  // Permission Errors (403)
  FORBIDDEN = 'FORBIDDEN',
  INSUFFICIENT_PERMISSIONS = 'INSUFFICIENT_PERMISSIONS',

  // Not Found Errors (404)
  NOT_FOUND = 'NOT_FOUND',
  RESOURCE_NOT_FOUND = 'RESOURCE_NOT_FOUND',

  // Rate Limiting (429)
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',

  // System Errors (500)
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  COMMAND_EXECUTION_FAILED = 'COMMAND_EXECUTION_FAILED',
  FILE_OPERATION_FAILED = 'FILE_OPERATION_FAILED',
  PROCESS_OPERATION_FAILED = 'PROCESS_OPERATION_FAILED',
  NETWORK_ERROR = 'NETWORK_ERROR',
  TIMEOUT = 'TIMEOUT',
}

// =====================================================================
// Authentication & Authorization
// =====================================================================

/**
 * JWT payload structure
 */
export interface JWTPayload {
  sub: string; // Subject (user/service ID)
  iat: number; // Issued at
  exp: number; // Expiration
  permissions: Permission[];
  metadata?: Record<string, any>;
}

/**
 * Permission system
 */
export enum Permission {
  // File operations
  FILE_READ = 'file:read',
  FILE_WRITE = 'file:write',
  FILE_DELETE = 'file:delete',
  FILE_EXECUTE = 'file:execute',

  // Process operations
  PROCESS_LIST = 'process:list',
  PROCESS_START = 'process:start',
  PROCESS_KILL = 'process:kill',
  PROCESS_MODIFY = 'process:modify',

  // System operations
  SYSTEM_INFO = 'system:info',
  SYSTEM_SHUTDOWN = 'system:shutdown',
  SYSTEM_MODIFY = 'system:modify',

  // Registry operations (Windows)
  REGISTRY_READ = 'registry:read',
  REGISTRY_WRITE = 'registry:write',
  REGISTRY_DELETE = 'registry:delete',

  // Network operations
  NETWORK_ACCESS = 'network:access',

  // Admin
  ADMIN = 'admin:*',
}

// =====================================================================
// Command Execution
// =====================================================================

/**
 * Command execution request
 */
export interface CommandExecutionRequest {
  command: string;
  args?: string[];
  options?: CommandExecutionOptions;
}

/**
 * Command execution options
 */
export interface CommandExecutionOptions {
  cwd?: string;
  env?: Record<string, string>;
  timeout?: number; // milliseconds
  shell?: boolean;
  maxBuffer?: number; // bytes
  killSignal?: string;
}

/**
 * Command execution result
 */
export interface CommandExecutionResult {
  stdout: string;
  stderr: string;
  exitCode: number;
  signal?: string;
  duration: number; // milliseconds
  pid?: number;
}

// =====================================================================
// File Operations
// =====================================================================

/**
 * File read request
 */
export interface FileReadRequest {
  path: string;
  encoding?: BufferEncoding;
  flag?: string;
}

/**
 * File write request
 */
export interface FileWriteRequest {
  path: string;
  content: string | Buffer;
  encoding?: BufferEncoding;
  mode?: number;
  flag?: string;
  atomic?: boolean; // Write to temp file then rename
}

/**
 * File copy request
 */
export interface FileCopyRequest {
  source: string;
  destination: string;
  overwrite?: boolean;
  preserveTimestamps?: boolean;
}

/**
 * File move request
 */
export interface FileMoveRequest {
  source: string;
  destination: string;
  overwrite?: boolean;
}

/**
 * File delete request
 */
export interface FileDeleteRequest {
  path: string;
  recursive?: boolean;
  force?: boolean;
}

/**
 * Directory list request
 */
export interface DirectoryListRequest {
  path: string;
  recursive?: boolean;
  filter?: string; // glob pattern
  includeHidden?: boolean;
}

/**
 * File search request
 */
export interface FileSearchRequest {
  path: string;
  query: string;
  searchContent?: boolean;
  searchFilename?: boolean;
  caseSensitive?: boolean;
  maxResults?: number;
}

/**
 * File stat information
 */
export interface FileInfo {
  path: string;
  name: string;
  size: number;
  isDirectory: boolean;
  isFile: boolean;
  isSymlink: boolean;
  createdAt: Date;
  modifiedAt: Date;
  accessedAt: Date;
  permissions: string;
  owner?: string;
}

/**
 * File watcher request
 */
export interface FileWatchRequest {
  path: string;
  recursive?: boolean;
  events?: ('add' | 'change' | 'unlink')[];
  callbackUrl?: string;
}

// =====================================================================
// Process Operations
// =====================================================================

/**
 * Process start request
 */
export interface ProcessStartRequest {
  executable: string;
  args?: string[];
  options?: CommandExecutionOptions;
  detached?: boolean;
}

/**
 * Process kill request
 */
export interface ProcessKillRequest {
  pid?: number;
  name?: string;
  signal?: string;
  force?: boolean;
}

/**
 * Process information
 */
export interface ProcessInfo {
  pid: number;
  name: string;
  cpu: number; // CPU usage percentage
  memory: number; // Memory usage in bytes
  ppid?: number; // Parent process ID
  command?: string;
  startTime?: Date;
  status?: string;
}

/**
 * Process priority request
 */
export interface ProcessPriorityRequest {
  pid: number;
  priority: number; // -20 to 19 (Unix) or priority class (Windows)
}

// =====================================================================
// System Operations
// =====================================================================

/**
 * System information
 */
export interface SystemInfo {
  platform: string;
  arch: string;
  release: string;
  hostname: string;
  uptime: number; // seconds
  cpu: {
    model: string;
    cores: number;
    speed: number; // MHz
    usage: number; // percentage
  };
  memory: {
    total: number; // bytes
    free: number; // bytes
    used: number; // bytes
    usagePercent: number;
  };
  disk: {
    total: number; // bytes
    free: number; // bytes
    used: number; // bytes
    usagePercent: number;
  }[];
  network: {
    interface: string;
    address: string;
    netmask: string;
    mac: string;
    internal: boolean;
  }[];
}

/**
 * System shutdown request
 */
export interface SystemShutdownRequest {
  action: 'shutdown' | 'restart' | 'sleep' | 'hibernate';
  delay?: number; // seconds
  force?: boolean;
  message?: string;
}

/**
 * System notification request
 */
export interface SystemNotificationRequest {
  title: string;
  message: string;
  icon?: string;
  sound?: boolean;
  priority?: 'low' | 'normal' | 'high' | 'critical';
}

/**
 * Clipboard operation request
 */
export interface ClipboardRequest {
  action: 'read' | 'write';
  content?: string;
  format?: 'text' | 'html' | 'rtf' | 'image';
}

/**
 * Screenshot request
 */
export interface ScreenshotRequest {
  format?: 'png' | 'jpg' | 'bmp';
  quality?: number; // 0-100
  display?: number; // Display index
  region?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

// =====================================================================
// Registry Operations (Windows)
// =====================================================================

/**
 * Registry read request
 */
export interface RegistryReadRequest {
  key: string;
  value?: string; // If not specified, read all values
  hive?: 'HKLM' | 'HKCU' | 'HKCR' | 'HKU' | 'HKCC';
}

/**
 * Registry write request
 */
export interface RegistryWriteRequest {
  key: string;
  value: string;
  data: string | number | boolean;
  type?: 'REG_SZ' | 'REG_DWORD' | 'REG_QWORD' | 'REG_BINARY' | 'REG_MULTI_SZ' | 'REG_EXPAND_SZ';
  hive?: 'HKLM' | 'HKCU' | 'HKCR' | 'HKU' | 'HKCC';
}

/**
 * Registry delete request
 */
export interface RegistryDeleteRequest {
  key: string;
  value?: string; // If not specified, delete entire key
  hive?: 'HKLM' | 'HKCU' | 'HKCR' | 'HKU' | 'HKCC';
}

/**
 * Registry backup request
 */
export interface RegistryBackupRequest {
  key: string;
  backupPath: string;
  hive?: 'HKLM' | 'HKCU' | 'HKCR' | 'HKU' | 'HKCC';
}

// =====================================================================
// Network Operations
// =====================================================================

/**
 * Ping request
 */
export interface PingRequest {
  host: string;
  count?: number;
  timeout?: number; // milliseconds
}

/**
 * Ping result
 */
export interface PingResult {
  host: string;
  alive: boolean;
  latency?: number; // milliseconds
  packetLoss?: number; // percentage
}

/**
 * File download request
 */
export interface FileDownloadRequest {
  url: string;
  destination: string;
  timeout?: number;
  headers?: Record<string, string>;
  callbackUrl?: string; // For progress updates
}

/**
 * Download progress
 */
export interface DownloadProgress {
  url: string;
  downloaded: number; // bytes
  total?: number; // bytes
  percent?: number;
  speed?: number; // bytes per second
  eta?: number; // seconds
}

// =====================================================================
// Audit Logging
// =====================================================================

/**
 * Audit log entry
 */
export interface AuditLogEntry {
  timestamp: Date;
  level: 'info' | 'warn' | 'error' | 'security';
  action: string;
  userId?: string;
  clientIp?: string;
  request?: {
    method: string;
    path: string;
    body?: any;
  };
  response?: {
    status: number;
    duration: number; // milliseconds
  };
  error?: {
    code: ErrorCode;
    message: string;
  };
  metadata?: Record<string, any>;
}

// =====================================================================
// Rate Limiting
// =====================================================================

/**
 * Rate limit configuration
 */
export interface RateLimitConfig {
  windowMs: number;
  maxRequests: number;
  keyGenerator?: (req: any) => string;
  skipSuccessfulRequests?: boolean;
  skipFailedRequests?: boolean;
}

/**
 * Rate limit info
 */
export interface RateLimitInfo {
  limit: number;
  remaining: number;
  reset: Date;
}

// =====================================================================
// Type Guards
// =====================================================================

/**
 * Type guard for CommandExecutionRequest
 */
export function isCommandExecutionRequest(obj: any): obj is CommandExecutionRequest {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    typeof obj.command === 'string'
  );
}

/**
 * Type guard for FileReadRequest
 */
export function isFileReadRequest(obj: any): obj is FileReadRequest {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    typeof obj.path === 'string'
  );
}

/**
 * Type guard for ProcessStartRequest
 */
export function isProcessStartRequest(obj: any): obj is ProcessStartRequest {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    typeof obj.executable === 'string'
  );
}
