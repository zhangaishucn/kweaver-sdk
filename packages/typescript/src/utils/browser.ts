import { spawn } from "node:child_process";

export function openBrowser(url: string): Promise<boolean> {
  const isWindows = process.platform === "win32";
  const command = process.platform === "darwin" ? "open" : isWindows ? "rundll32.exe" : "xdg-open";
  const args = isWindows
    ? [
        "url.dll,FileProtocolHandler",
        url,
      ]
    : [url];

  return new Promise((resolve) => {
    const child = spawn(command, args, {
      stdio: "ignore",
      detached: !isWindows,
      windowsHide: true,
    });

    child.once("error", () => resolve(false));
    child.once("spawn", () => resolve(true));

    if (!isWindows) {
      child.unref();
    }
  });
}
