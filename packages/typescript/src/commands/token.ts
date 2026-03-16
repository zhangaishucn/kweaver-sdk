import { ensureValidToken, formatHttpError } from "../auth/oauth.js";

export function parseTokenArgs(args: string[]): void {
  if (args.length > 0) {
    throw new Error("Usage: kweaver token");
  }
}

export async function runTokenCommand(args: string[]): Promise<number> {
  try {
    parseTokenArgs(args);
  } catch (error) {
    console.error(formatHttpError(error));
    return 1;
  }

  try {
    const token = await ensureValidToken();
    console.log(token.accessToken);
    return 0;
  } catch (error) {
    console.error(formatHttpError(error));
    return 1;
  }
}
