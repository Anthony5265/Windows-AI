/**
 * System Operations Service
 * System information, process management, and OS integration
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import os from 'os';
import {
  SystemInfo,
  ProcessInfo,
  ProcessStartRequest,
  ProcessKillRequest,
  SystemNotificationRequest,
} from '../types/index.js';
import {
  ProcessOperationError,
  ValidationError,
} from '../errors.js';
import { CommandExecutor } from './command-executor.js';
import { logProcessOperation } from '../middleware/audit.js';

const execPromise = promisify(exec);

/**
 * System operations service
 */
export class SystemOperations {
  /**
   * Get comprehensive system information
   */
  public static async getSystemInfo(userId?: string): Promise<SystemInfo> {
    const cpuInfo = os.cpus();
    const totalMem = os.totalmem();
    const freeMem = os.freemem();
    const usedMem = totalMem - freeMem;

    // Get network interfaces
    const networkInterfaces = os.networkInterfaces();
    const network = Object.entries(networkInterfaces).flatMap(([iface, addresses]) =>
      (addresses || []).map((addr) => ({
        interface: iface,
        address: addr.address,
        netmask: addr.netmask,
        mac: addr.mac,
        internal: addr.internal,
      }))
    );

    // Get disk information (platform-specific)
    const disk = await this.getDiskInfo();

    return {
      platform: os.platform(),
      arch: os.arch(),
      release: os.release(),
      hostname: os.hostname(),
      uptime: os.uptime(),
      cpu: {
        model: cpuInfo[0]?.model || 'Unknown',
        cores: cpuInfo.length,
        speed: cpuInfo[0]?.speed || 0,
        usage: await this.getCPUUsage(),
      },
      memory: {
        total: totalMem,
        free: freeMem,
        used: usedMem,
        usagePercent: (usedMem / totalMem) * 100,
      },
      disk,
      network,
    };
  }

  /**
   * Get CPU usage percentage
   */
  private static async getCPUUsage(): Promise<number> {
    // Simple CPU usage calculation
    const cpus1 = os.cpus();
    const idle1 = cpus1.reduce((acc, cpu) => acc + cpu.times.idle, 0);
    const total1 = cpus1.reduce(
      (acc, cpu) => acc + Object.values(cpu.times).reduce((a, b) => a + b, 0),
      0
    );

    // Wait 100ms
    await new Promise((resolve) => setTimeout(resolve, 100));

    const cpus2 = os.cpus();
    const idle2 = cpus2.reduce((acc, cpu) => acc + cpu.times.idle, 0);
    const total2 = cpus2.reduce(
      (acc, cpu) => acc + Object.values(cpu.times).reduce((a, b) => a + b, 0),
      0
    );

    const idleDiff = idle2 - idle1;
    const totalDiff = total2 - total1;

    return ((1 - idleDiff / totalDiff) * 100) || 0;
  }

  /**
   * Get disk information (platform-specific)
   */
  private static async getDiskInfo(): Promise<Array<{
    total: number;
    free: number;
    used: number;
    usagePercent: number;
  }>> {
    try {
      const isWindows = process.platform === 'win32';

      if (isWindows) {
        // Windows: use wmic
        const { stdout } = await execPromise(
          'wmic logicaldisk get size,freespace,caption'
        );
        const lines = stdout.trim().split('\n').slice(1);

        return lines
          .map((line) => {
            const [, free, total] = line.trim().split(/\s+/);
            const freeNum = parseInt(free, 10) || 0;
            const totalNum = parseInt(total, 10) || 0;
            const usedNum = totalNum - freeNum;

            return {
              total: totalNum,
              free: freeNum,
              used: usedNum,
              usagePercent: totalNum > 0 ? (usedNum / totalNum) * 100 : 0,
            };
          })
          .filter((d) => d.total > 0);
      } else {
        // Unix/Linux: use df
        const { stdout } = await execPromise('df -k /');
        const lines = stdout.trim().split('\n').slice(1);

        return lines.map((line) => {
          const [, total, used, free] = line.trim().split(/\s+/);
          const totalNum = parseInt(total, 10) * 1024 || 0;
          const usedNum = parseInt(used, 10) * 1024 || 0;
          const freeNum = parseInt(free, 10) * 1024 || 0;

          return {
            total: totalNum,
            free: freeNum,
            used: usedNum,
            usagePercent: totalNum > 0 ? (usedNum / totalNum) * 100 : 0,
          };
        });
      }
    } catch (error) {
      // Return empty array if disk info unavailable
      return [];
    }
  }

  /**
   * List running processes
   */
  public static async listProcesses(userId?: string): Promise<{ processes: ProcessInfo[] }> {
    try {
      const isWindows = process.platform === 'win32';

      if (isWindows) {
        // Windows: use tasklist
        const result = await CommandExecutor.executeShell('tasklist /fo csv /nh', {}, userId);
        const processes = this.parseWindowsTasklist(result.stdout);
        return { processes };
      } else {
        // Unix/Linux: use ps
        const result = await CommandExecutor.executeShell(
          'ps aux --no-headers',
          {},
          userId
        );
        const processes = this.parseUnixPs(result.stdout);
        return { processes };
      }
    } catch (error) {
      throw new ProcessOperationError('list', {
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  /**
   * Parse Windows tasklist output
   */
  private static parseWindowsTasklist(output: string): ProcessInfo[] {
    const lines = output.trim().split('\n');
    return lines.map((line) => {
      const [name, pid, , , mem] = line.split(',').map((s) => s.replace(/"/g, '').trim());
      return {
        pid: parseInt(pid, 10) || 0,
        name,
        cpu: 0, // Not available in tasklist
        memory: parseInt(mem.replace(/[^\d]/g, ''), 10) * 1024 || 0,
      };
    });
  }

  /**
   * Parse Unix ps output
   */
  private static parseUnixPs(output: string): ProcessInfo[] {
    const lines = output.trim().split('\n');
    return lines.map((line) => {
      const parts = line.trim().split(/\s+/);
      const [, pid, cpu, mem, , , , , , , command] = parts;

      return {
        pid: parseInt(pid, 10) || 0,
        name: command || 'unknown',
        cpu: parseFloat(cpu) || 0,
        memory: parseFloat(mem) * 10240 || 0, // Approximate
        command,
      };
    });
  }

  /**
   * Start a process
   */
  public static async startProcess(
    request: ProcessStartRequest,
    userId?: string
  ): Promise<{ pid: number; ok: boolean }> {
    try {
      const result = await CommandExecutor.execute(
        {
          command: request.executable,
          args: request.args,
          options: {
            ...request.options,
            timeout: request.options?.timeout || 60000,
          },
        },
        userId
      );

      logProcessOperation('start', request.executable, userId, true, {
        pid: result.pid,
      });

      return { pid: result.pid || 0, ok: true };
    } catch (error) {
      logProcessOperation('start', request.executable, userId, false, {
        error: error instanceof Error ? error.message : String(error),
      });
      throw new ProcessOperationError('start', {
        executable: request.executable,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  /**
   * Kill a process
   */
  public static async killProcess(
    request: ProcessKillRequest,
    userId?: string
  ): Promise<{ ok: boolean }> {
    try {
      const isWindows = process.platform === 'win32';
      let command: string;

      if (request.pid) {
        command = isWindows
          ? `taskkill /PID ${request.pid}${request.force ? ' /F' : ''}`
          : `kill ${request.signal || '-TERM'} ${request.pid}`;
      } else if (request.name) {
        command = isWindows
          ? `taskkill /IM ${request.name}${request.force ? ' /F' : ''}`
          : `killall ${request.signal || '-TERM'} ${request.name}`;
      } else {
        throw new ValidationError('Either pid or name must be provided');
      }

      await CommandExecutor.executeShell(command, {}, userId);

      const target = request.pid || request.name || 'unknown';
      logProcessOperation('kill', target, userId, true, {
        signal: request.signal,
        force: request.force,
      });

      return { ok: true };
    } catch (error) {
      const target = request.pid || request.name || 'unknown';
      logProcessOperation('kill', target, userId, false, {
        error: error instanceof Error ? error.message : String(error),
      });
      throw new ProcessOperationError('kill', {
        target: request.pid || request.name,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  /**
   * Display system notification
   */
  public static async showNotification(
    request: SystemNotificationRequest,
    userId?: string
  ): Promise<{ ok: boolean }> {
    try {
      const isWindows = process.platform === 'win32';
      const isMac = process.platform === 'darwin';

      if (isWindows) {
        // Windows: use PowerShell
        const script = `
          Add-Type -AssemblyName System.Windows.Forms;
          $notify = New-Object System.Windows.Forms.NotifyIcon;
          $notify.Icon = [System.Drawing.SystemIcons]::Information;
          $notify.Visible = $true;
          $notify.ShowBalloonTip(5000, "${request.title}", "${request.message}", [System.Windows.Forms.ToolTipIcon]::Info);
        `;
        await CommandExecutor.executeShell(`powershell -Command "${script}"`, {}, userId);
      } else if (isMac) {
        // macOS: use osascript
        await CommandExecutor.executeShell(
          `osascript -e 'display notification "${request.message}" with title "${request.title}"'`,
          {},
          userId
        );
      } else {
        // Linux: use notify-send
        await CommandExecutor.executeShell(
          `notify-send "${request.title}" "${request.message}"`,
          {},
          userId
        );
      }

      return { ok: true };
    } catch (error) {
      throw new ProcessOperationError('notification', {
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }
}
