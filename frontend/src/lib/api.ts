import type { ApiErrorPayload } from "@/types/auth";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details: unknown = null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const payload = (await response.json()) as ApiErrorPayload & { detail?: unknown };
    const validationMessage = formatValidationMessage(payload.detail);
    return new ApiError(
      response.status,
      payload.code ?? (validationMessage ? "REQUEST_VALIDATION_FAILED" : "API_ERROR"),
      payload.message ?? validationMessage ?? "Une erreur est survenue.",
      payload.details ?? payload.detail ?? null,
    );
  } catch {
    return new ApiError(
      response.status,
      "API_ERROR",
      "Le serveur a retourné une réponse inattendue.",
    );
  }
}

function formatValidationMessage(detail: unknown): string | null {
  if (!Array.isArray(detail) || detail.length === 0) return null;
  const first = detail[0];
  if (!first || typeof first !== "object") return null;
  const location = (first as { loc?: unknown }).loc;
  const field = Array.isArray(location)
    ? location.filter((part): part is string => typeof part === "string" && part !== "body").at(-1)
    : null;
  return field
    ? `La valeur du champ « ${field} » est invalide. Vérifiez les informations saisies.`
    : "Certaines informations saisies sont invalides. Vérifiez le formulaire.";
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
