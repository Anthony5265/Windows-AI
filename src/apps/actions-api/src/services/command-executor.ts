/**
 * Secure Command Execution Engine
 * Provides sandboxed, monitored command execution with resource limits
 */

import { spawn, exec, SpawnOptions } from 'child_process';
import { promisify } from 'util';
import {
  CommandExecutionRequest,
  CommandExecutionResult,
  CommandExecutionOptions,
} from '../types/index.js';
import {
  CommandExecutionError,
  TimeoutError,
  ValidationError,
} from '../errors.js';
import { validateCommand, sanitizePath } from '../middleware/security.js';
import { logCommandExecution } from '../middleware/audit.js';

const execPromise = promisify(exec);

// =====================================================================
// Command Whitelist
// =====================================================================

/**
 * Whitelist of allowed commands (security critical)
 * Only these commands can be executed
 */
const ALLOWED_COMMANDS = new Set([
  // File operations
  'ls', 'dir', 'cat', 'type', 'head', 'tail', 'find', 'where',

  // System info
  'echo', 'pwd', 'cd', 'hostname', 'whoami', 'date', 'time',
  'systeminfo', 'wmic', 'tasklist', 'ps',

  // Network
  'ping', 'ipconfig', 'ifconfig', 'netstat', 'nslookup',

  // Process
  'taskkill', 'kill',

  // PowerShell (with restrictions)
  'powershell', 'pwsh',

  // Python/Node (for scripts)
  'python', 'python3', 'node',

  // Custom Windows-AI scripts (whitelisted)
  'windows-ai-script',
]);

/**
 * Dangerous command patterns to block
 */
const DANGEROUS_PATTERNS = [
  /rm\s+-rf/i, // Recursive delete
  /format\s+[a-z]:/i, // Format drive
  /del\s+\/[sq]/i, // Silent/recursive delete
  /shutdown/i, // System shutdown (unless explicitly allowed)
  /reboot/i, // System reboot
  /mkfs/i, // Format filesystem
  /dd\s+if=/i, // Disk duplication (can be dangerous)
];

// =====================================================================
// Command Executor
// =====================================================================

export class CommandExecutor {
  private static readonly DEFAULT_TIMEOUT = 30000; // 30 seconds
  private static readonly MAX_BUFFER = 10 * 1024 * 1024; // 10MB
  private static readonly MAX_TIMEOUT = 300000; // 5 minutes

  /**
   * Execute a command securely with sandboxing and resource limits
   */
  public static async execute(
    request: CommandExecutionRequest,
    userId?: string
  ): Promise<CommandExecutionResult> {
    const startTime = Date.now();
    const { command, args = [], options = {} } = request;

    try {
      // Validate command
      this.validateCommand(command, args);

      // Sanitize options
      const sanitizedOptions = this.sanitizeOptions(options);

      // Execute command
      const result = await this.executeInternal(command, args, sanitizedOptions);

      // Log successful execution
      logCommandExecution(
        `${command} ${args.join(' ')}`,
        userId,
        true,
        {
          exitCode: result.exitCode,
          duration: result.duration,
        }
      );

      return result;
    } catch (error) {
      // Log failed execution
      logCommandExecution(
        `${command} ${args.join(' ')}`,
        userId,
        false,
        {
          error: error instanceof Error ? error.message : String(error),
          duration: Date.now() - startTime,
        }
      );

      throw error;
    }
  }

  /**
   * Validate command against whitelist and dangerous patterns
   */
  private static validateCommand(command: string, args: string[]): void {
    // Check if command is in whitelist
    const baseCommand = command.split(/[\\/]/).pop()!.toLowerCase();
    if (!ALLOWED_COMMANDS.has(baseCommand)) {
      throw new ValidationError(`Command not allowed: ${command}`, {
        command: baseCommand,
        whitelist: Array.from(ALLOWED_COMMANDS),
      });
    }

    // Validate command string
    validateCommand(command);

    // Check for dangerous patterns in full command
    const fullCommand = `${command} ${args.join(' ')}`;
    for (const pattern of DANGEROUS_PATTERNS) {
      if (pattern.test(fullCommand)) {
        throw new ValidationError(`Command contains dangerous pattern: ${pattern}`, {
          command: fullCommand,
          pattern: pattern.toString(),
        });
      }
    }

    // Validate arguments
    for (const arg of args) {
      if (arg.includes('..') || arg.includes('~')) {
        throw new ValidationError('Arguments contain path traversal attempts', {
          arg,
        });
      }
    }
  }

  /**
   * Sanitize execution options
   */
  private static sanitizeOptions(options: CommandExecutionOptions): SpawnOptions {
    const timeout = Math.min(
      options.timeout || this.DEFAULT_TIMEOUT,
      this.MAX_TIMEOUT
    );

    const sanitized: SpawnOptions = {
      timeout,
      maxBuffer: Math.min(options.maxBuffer || this.MAX_BUFFER, this.MAX_BUFFER),
      killSignal: options.killSignal || 'SIGTERM',
      windowsHide: true, // Hide windows on Windows platform
    };

    // Sanitize working directory
    if (options.cwd) {
      sanitized.cwd = sanitizePath(options.cwd);
    }

    // Sanitize environment variables
    if (options.env) {
      sanitized.env = this.sanitizeEnv(options.env);
    }

    return sanitized;
  }

  /**
   * Sanitize environment variables
   */
  private static sanitizeEnv(env: Record<string, string>): Record<string, string> {
    const sanitized: Record<string, string> = { ...process.env };

    // Remove dangerous environment variables
    delete sanitized.LD_PRELOAD;
    delete sanitized.LD_LIBRARY_PATH;
    delete sanitized.DYLD_INSERT_LIBRARIES;

    // Add user-provided env vars (with validation)
    for (const [key, value] of Object.entries(env)) {
      if (!/^[A-Z_][A-Z0-9_]*$/i.test(key)) {
        throw new ValidationError(`Invalid environment variable name: ${key}`);
      }
      sanitized[key] = value;
    }

    return sanitized;
  }

  /**
   * Execute command internally
   */
  private static async executeInternal(
    command: string,
    args: string[],
    options: SpawnOptions
  ): Promise<CommandExecutionResult> {
    const startTime = Date.now();

    return new Promise((resolve, reject) => {
      const child = spawn(command, args, options);

      let stdout = '';
      let stderr = '';
      let timedOut = false;

      // Set up timeout
      const timeout = options.timeout || this.DEFAULT_TIMEOUT;
      const timer = setTimeout(() => {
        timedOut = true;
        child.kill(options.killSignal as any || 'SIGTERM');

        // Force kill after grace period
        setTimeout(() => {
          if (!child.killed) {
            child.kill('SIGKILL');
          }
        }, 5000);
      }, timeout);

      // Capture stdout
      if (child.stdout) {
        child.stdout.on('data', (data) => {
          stdout += data.toString();
          // Prevent memory overflow
          if (stdout.length > (options.maxBuffer || this.MAX_BUFFER)) {
            child.kill();
            reject(new CommandExecutionError('Output buffer exceeded', {
              maxBuffer: options.maxBuffer || this.MAX_BUFFER,
            }));
          }
        });
      }

      // Capture stderr
      if (child.stderr) {
        child.stderr.on('data', (data) => {
          stderr += data.toString();
        });
      }

      // Handle errors
      child.on('error', (err) => {
        clearTimeout(timer);
        reject(
          new CommandExecutionError(`Command execution failed: ${err.message}`, {
            error: err.message,
            command,
            args,
          })
        );
      });

      // Handle completion
      child.on('close', (code, signal) => {
        clearTimeout(timer);

        const duration = Date.now() - startTime;

        if (timedOut) {
          reject(new TimeoutError('Command execution', timeout, {
            command,
            args,
            duration,
          }));
          return;
        }

        resolve({
          stdout: stdout.trim(),
          stderr: stderr.trim(),
          exitCode: code || 0,
          signal: signal || undefined,
          duration,
          pid: child.pid,
        });
      });
    });
  }

  /**
   * Execute a shell command (use with extreme caution)
   */
  public static async executeShell(
    command: string,
    options: CommandExecutionOptions = {},
    userId?: string
  ): Promise<CommandExecutionResult> {
    const startTime = Date.now();

    try {
      // Validate command
      validateCommand(command);

      // Check whitelist for base command
      const baseCommand = command.split(/\s+/)[0].split(/[\\/]/).pop()!.toLowerCase();
      if (!ALLOWED_COMMANDS.has(baseCommand)) {
        throw new ValidationError(`Command not allowed: ${baseCommand}`);
      }

      // Execute with timeout
      const timeout = Math.min(
        options.timeout || this.DEFAULT_TIMEOUT,
        this.MAX_TIMEOUT
      );

      const { stdout, stderr } = await execPromise(command, {
        timeout,
        maxBuffer: Math.min(options.maxBuffer || this.MAX_BUFFER, this.MAX_BUFFER),
        cwd: options.cwd ? sanitizePath(options.cwd) : undefined,
        env: options.env ? this.sanitizeEnv(options.env) : undefined,
      });

      const duration = Date.now() - startTime;

      logCommandExecution(command, userId, true, {
        exitCode: 0,
        duration,
      });

      return {
        stdout: stdout.trim(),
        stderr: stderr.trim(),
        exitCode: 0,
        duration,
      };
    } catch (error: any) {
      const duration = Date.now() - startTime;

      logCommandExecution(command, userId, false, {
        error: error.message,
        duration,
      });

      if (error.killed) {
        throw new TimeoutError('Shell command', options.timeout || this.DEFAULT_TIMEOUT, {
          command,
          duration,
        });
      }

      throw new CommandExecutionError(error.message || 'Shell command failed', {
        command,
        exitCode: error.code,
        stderr: error.stderr,
        duration,
      });
    }
  }
}
