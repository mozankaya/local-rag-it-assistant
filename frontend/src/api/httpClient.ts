export type ApiErrorKind = "http" | "network";
export type AuthMode = "none" | "optional" | "required";

interface ApiErrorOptions {
  status?: number;
  detail?: string;
  responseDetails?: unknown;
  kind: ApiErrorKind;
  cause?: unknown;
}

export class ApiError extends Error {
  readonly status?: number;
  readonly detail?: string;
  readonly responseDetails?: unknown;
  readonly kind: ApiErrorKind;
  readonly cause?: unknown;

  constructor(message: string, status: number);
  constructor(message: string, options: ApiErrorOptions);
  constructor(message: string, optionsOrStatus: ApiErrorOptions | number) {
    super(message);
    const options = typeof optionsOrStatus === "number"
      ? { kind: "http" as const, status: optionsOrStatus }
      : optionsOrStatus;

    this.name = "ApiError";
    this.status = options.status;
    this.detail = options.detail;
    this.responseDetails = options.responseDetails;
    this.kind = options.kind;
    this.cause = options.cause;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

export interface HttpRequestOptions {
  method?: string;
  headers?: HeadersInit;
  body?: BodyInit | null;
  auth?: AuthMode;
  requiredAuthMessage?: string;
  fallbackErrorMessage: (status: number) => string;
  parseErrorBody?: boolean;
  useDetailAsMessage?: boolean;
}

function mergeAuthHeader(
  headers: HeadersInit | undefined,
  auth: AuthMode,
  missingAuthMessage: string | undefined,
): Headers {
  const mergedHeaders = new Headers();

  if (auth !== "none") {
    const token = localStorage.getItem("access_token");

    if (!token && auth === "required") {
      throw new Error(missingAuthMessage ?? "Access token not found.");
    }

    if (token) {
      mergedHeaders.set("Authorization", `Bearer ${token}`);
    }
  }

  if (headers) {
    new Headers(headers).forEach((value, key) => {
      mergedHeaders.set(key, value);
    });
  }

  return mergedHeaders;
}

async function parseErrorDetails(response: Response): Promise<unknown> {
  try {
    return await response.json() as unknown;
  } catch {
    return undefined;
  }
}

function getStringDetail(responseDetails: unknown): string | undefined {
  if (
    typeof responseDetails === "object"
    && responseDetails !== null
    && "detail" in responseDetails
    && typeof responseDetails.detail === "string"
  ) {
    return responseDetails.detail;
  }

  return undefined;
}

async function request(
  url: string,
  options: HttpRequestOptions,
): Promise<Response> {
  const headers = mergeAuthHeader(
    options.headers,
    options.auth ?? "required",
    options.requiredAuthMessage,
  );

  let response: Response;

  try {
    response = await fetch(url, {
      method: options.method,
      headers,
      body: options.body,
    });
  } catch (cause) {
    const message = cause instanceof Error
      ? cause.message
      : "Network request failed.";

    throw new ApiError(message, {
      kind: "network",
      cause,
    });
  }

  if (!response.ok) {
    const responseDetails = options.parseErrorBody
      ? await parseErrorDetails(response)
      : undefined;
    const detail = getStringDetail(responseDetails);
    const fallbackMessage = options.fallbackErrorMessage(response.status);

    throw new ApiError(
      options.useDetailAsMessage && detail ? detail : fallbackMessage,
      {
        kind: "http",
        status: response.status,
        detail,
        responseDetails,
      },
    );
  }

  return response;
}

export async function requestJson<T>(
  url: string,
  options: HttpRequestOptions,
): Promise<T> {
  const response = await request(url, options);
  return response.json() as Promise<T>;
}

export async function requestBlob(
  url: string,
  options: HttpRequestOptions,
): Promise<Blob> {
  const response = await request(url, options);
  return response.blob();
}

export async function requestEmpty(
  url: string,
  options: HttpRequestOptions,
): Promise<void> {
  await request(url, options);
}
