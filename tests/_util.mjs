
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

const VERSION_PATTERN = /Python\s+(\d+)\.(\d+)(?:\.(\d+))?/i;
const MIN_SUPPORTED_MAJOR = 3;

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

function cloneCandidate(candidate) {
  return {
    cmd: candidate.cmd,
    runArgs: [...candidate.runArgs],
    detectArgs: [...candidate.detectArgs],
  };
}

function resolveCandidates() {
  const envCmd = process.env.PYTHON?.trim();
  const resolved = [];

  if (envCmd) {
    const [cmd, ...args] = splitCommandLine(envCmd);
    if (cmd) {
      resolved.push({
        cmd,
        runArgs: args,
        detectArgs: [...args, '--version'],
      });
    }
  }

  for (const candidate of DEFAULT_CANDIDATES) {
    resolved.push(cloneCandidate(candidate));
  }

  const seen = new Set();
  const unique = [];

  for (const candidate of resolved) {
    const key = `${candidate.cmd}\u0000${candidate.runArgs.join('\u0000')}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    unique.push(candidate);
  }

  return unique;
}

function parsePythonVersion(output) {
  if (!output) {
    return null;
  }

  const match = output.match(VERSION_PATTERN);
  if (!match) {
    return null;
  }

  return {
    major: Number.parseInt(match[1], 10),
    minor: Number.parseInt(match[2], 10),
    patch: match[3] ? Number.parseInt(match[3], 10) : null,
  };
}

function isSupportedVersion(version) {
  if (!version || Number.isNaN(version.major)) {
    return false;
  }

  if (version.major < MIN_SUPPORTED_MAJOR) {
    return false;
  }

  return true;
}

function probePython(candidate) {
  const result = spawnSync(candidate.cmd, candidate.detectArgs, { encoding: 'utf8' });

  if (result.error || result.signal) {
    return null;
  }

  if (typeof result.status === 'number' && result.status !== 0) {
    return null;
  }

  const combinedOutput = `${result.stdout ?? ''}${result.stderr ?? ''}`.trim();
  const version = parsePythonVersion(combinedOutput);

  if (!isSupportedVersion(version)) {
    return null;
  }

  return {
    version,
    rawOutput: combinedOutput,
  };
}

export function detectPython() {
  for (const candidate of resolveCandidates()) {
    const probe = probePython(candidate);
    if (probe) {
      return {
        cmd: candidate.cmd,
        args: [...candidate.runArgs],
        version: probe.version,
        versionOutput: probe.rawOutput,
      };
    }
  }

  return { cmd: 'python', args: [] };
}

