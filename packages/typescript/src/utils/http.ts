export class HttpError extends Error {
  readonly status: number;
  readonly statusText: string;
  readonly body: string;

  constructor(status: number, statusText: string, body: string) {
    super(`HTTP ${status} ${statusText}`);
    this.name = "HttpError";
    this.status = status;
    this.statusText = statusText;
    this.body = body;
  }
}

export class NetworkRequestError extends Error {
  readonly method: string;
  readonly url: string;
  readonly causeMessage: string;
  readonly hint: string;

  constructor(method: string, url: string, causeMessage: string, hint: string) {
    super(`Network request failed`);
    this.name = "NetworkRequestError";
    this.method = method;
    this.url = url;
    this.causeMessage = causeMessage;
    this.hint = hint;
  }
}

function buildNetworkHint(causeMessage: string): string {
  const normalized = causeMessage.toLowerCase();

  if (
    normalized.includes("enotfound") ||
    normalized.includes("eai_again") ||
    normalized.includes("getaddrinfo")
  ) {
    return "DNS lookup failed. Check whether the domain is correct and reachable from your network.";
  }

  if (
    normalized.includes("certificate") ||
    normalized.includes("self signed") ||
    normalized.includes("hostname") ||
    normalized.includes("tls")
  ) {
    return "TLS handshake failed. Check the HTTPS certificate and whether the host supports this domain.";
  }

  if (
    normalized.includes("econnrefused") ||
    normalized.includes("econnreset") ||
    normalized.includes("socket") ||
    normalized.includes("network is unreachable")
  ) {
    return "The host could not be reached. Check connectivity, firewall rules, and whether the service is listening.";
  }

  return "Check whether the platform URL is correct and whether it exposes /oauth2/clients over HTTPS.";
}

export async function fetchTextOrThrow(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<{ response: Response; body: string }> {
  let response: Response;
  try {
    response = await fetch(input, init);
  } catch (error) {
    const url =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.toString()
          : input.url;
    const causeMessage =
      error instanceof Error && "cause" in error && error.cause instanceof Error
        ? error.cause.message
        : error instanceof Error
          ? error.message
          : String(error);
    const method = init?.method ?? "GET";
    throw new NetworkRequestError(method, url, causeMessage, buildNetworkHint(causeMessage));
  }

  const body = await response.text();

  if (!response.ok) {
    throw new HttpError(response.status, response.statusText, body);
  }

  return { response, body };
}
