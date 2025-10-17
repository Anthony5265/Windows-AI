import { spawnSync } from 'child_process';

const CANDIDATES = [
  {
    cmd: 'python',
    runArgs: [],
    detectArgs: ['--version'],
  },
  {
    cmd: 'python3',
    runArgs: [],
    detectArgs: ['--version'],
  },
  {
    cmd: 'py',
    runArgs: ['-3'],
    detectArgs: ['-3', '--version'],
  },
];

export function detectPython() {
  for (const candidate of CANDIDATES) {
    const result = spawnSync(candidate.cmd, candidate.detectArgs, { encoding: 'utf8' });
    if (
      result.status === 0 ||
      (result.stdout && result.stdout.includes('Python')) ||
      (result.stderr && result.stderr.includes('Python'))
    ) {
      return { cmd: candidate.cmd, args: candidate.runArgs };
    }
  }

  return { cmd: 'python', args: [] };
}
