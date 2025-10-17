
import { spawnSync } from 'child_process';

const DEFAULT_CANDIDATES = [
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

function splitCommandLine(spec) {
  const segments = [];
  let current = '';
  let quote = null;
  let escape = false;

  for (const ch of spec) {
    if (escape) {
      current += ch;
      escape = false;
      continue;
    }

    if (ch === '\\' && quote !== "'") {
      escape = true;
      continue;
    }

    if (quote) {
      if (ch === quote) {
        quote = null;
      } else {
        current += ch;
      }
      continue;
    }

    if (ch === '"' || ch === "'") {
      quote = ch;
      continue;
    }

    if (!quote && /\s/.test(ch)) {
      if (current) {
        segments.push(current);
        current = '';
      }
      continue;
    }

    current += ch;
  }

  if (escape) {
    current += '\\';
  }

  if (current) {
    segments.push(current);
  }

  return segments;
}

function resolveCandidates() {
  const envCmd = process.env.PYTHON?.trim();
  if (!envCmd) {
    return DEFAULT_CANDIDATES;
  }

  const [cmd, ...args] = splitCommandLine(envCmd);
  if (!cmd) {
    return DEFAULT_CANDIDATES;
  }

  return [
    {
      cmd,
      runArgs: args,
      detectArgs: [...args, '--version'],
    },
    ...DEFAULT_CANDIDATES,
  ];
}

function isPythonCandidate(candidate) {
  const result = spawnSync(candidate.cmd, candidate.detectArgs, { encoding: 'utf8' });

  if (result.error) {
    return false;
  }

  if (typeof result.status === 'number' && result.status !== 0) {
    return false;
  }

  const combinedOutput = `${result.stdout ?? ''}${result.stderr ?? ''}`;
  return /Python/i.test(combinedOutput);
}

export function detectPython() {
  for (const candidate of resolveCandidates()) {
    if (isPythonCandidate(candidate)) {
      return { cmd: candidate.cmd, args: [...candidate.runArgs] };
    }
  }

  return { cmd: 'python', args: [] };
}

