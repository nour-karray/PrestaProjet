import type { ApiErrorPayload } from "@/types/auth";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return new ApiError(
      response.status,
      payload.code ?? "API_ERROR",
      payload.message ?? "Une erreur est survenue.",
    );
  } catch {
    return new ApiError(
      response.status,
      "API_ERROR",
      "Le serveur a retourné une réponse inattendue.",
    );
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  allowRefresh = true,
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${apiUrl}${path}`, {
      ...options,
      credentials: "include",
      headers: {
        ...(options.body instanceof FormData
          ? {}
          : { "Content-Type": "application/json" }),
        ...options.headers,
      },
    });
  } catch {
    throw new ApiError(
      0,
      "SERVER_UNAVAILABLE",
      "Le serveur est indisponible. Vérifiez que le backend est démarré.",
    );
  }

  if (
    response.status === 401 &&
    allowRefresh &&
    path !== "/api/auth/login" &&
    path !== "/api/auth/refresh"
  ) {
    const refreshResponse = await fetch(`${apiUrl}/api/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (refreshResponse.ok) {
      return apiRequest<T>(path, options, false);
    }
  }

  if (!response.ok) {
    throw await parseError(response);
  }

  return (await response.json()) as T;
}
