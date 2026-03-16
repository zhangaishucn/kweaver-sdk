import { spawn } from "node:child_process";

export function openBrowser(url: string): Promise<boolean> {
  const command =
    process.platform === "darwin"
      ? "open"
      : process.platform === "win32"
        ? "cmd"
        : "xdg-open";

  const args =
    process.platform === "win32"
      ? ["/c", "start", "", url]
      : [url];

  return new Promise((resolve) => {
    const child = spawn(command, args, {
      detached: true,
      stdio: "ignore",
    });

    child.on("error", () => resolve(false));
    child.unref();
    resolve(true);
  });
}
