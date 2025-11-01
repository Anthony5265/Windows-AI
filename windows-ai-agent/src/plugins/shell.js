import { spawn } from "child_process";
export function exec(command, options = {}) {
  return new Promise((resolve, reject) => {
    const isWin = process.platform === "win32";
    const shell = isWin ? "powershell.exe" : "bash";
    const arg = isWin ? ["-NoProfile", "-Command", command] : ["-lc", command];
    const child = spawn(shell, arg, { stdio: "pipe", ...options });
    let out = "",
      err = "";
    child.stdout.on("data", (d) => (out += d.toString()));
    child.stderr.on("data", (d) => (err += d.toString()));
    child.on("close", (code) => {
      if (code === 0) resolve({ status: "ok", code, out });
      else reject(new Error(err || `exit ${code}`));
    });
  });
}
