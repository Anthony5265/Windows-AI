import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs/promises';
import os from 'os';

const execAsync = promisify(exec);

export interface ActionRequest {
  action: string;
  params?: Record<string, any>;
}

export async function executeAction(req: ActionRequest): Promise<any> {
  switch (req.action) {
    case 'shell': {
      const cmd = req.params?.command;
      if (!cmd) throw new Error('Missing command');
      const { stdout } = await execAsync(cmd, { timeout: req.params?.timeout_ms ?? 10000 });
      return { stdout };
    }
    case 'read_file': {
      const path = req.params?.path;
      if (!path) throw new Error('Missing path');
      return { content: await fs.readFile(path, 'utf8') };
    }
    case 'write_file': {
      const path = req.params?.path;
      if (!path) throw new Error('Missing path');
      const content = req.params?.content ?? '';
      await fs.writeFile(path, content, 'utf8');
      return { ok: true };
    }
    case 'get_system_info': {
      return {
        platform: os.platform(),
        arch: os.arch(),
        release: os.release()
      };
    }
    default:
      throw new Error(`Unknown action: ${req.action}`);
  }
}
