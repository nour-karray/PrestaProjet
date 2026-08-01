import { apiRequest } from "@/lib/api";
import type { Administrator, AuthResponse } from "@/types/auth";

export function login(email: string, password: string): Promise<AuthResponse> {
  return apiRequest<AuthResponse>(
    "/api/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ email, password }),
    },
    false,
  );
}

export function getCurrentAdministrator(): Promise<Administrator> {
  return apiRequest<Administrator>("/api/auth/me");
}

export function logout(): Promise<{ message: string }> {
  return apiRequest<{ message: string }>(
    "/api/auth/logout",
    { method: "POST" },
    false,
  );
}

