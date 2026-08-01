export type Administrator = {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
};

export type AuthResponse = {
  administrator: Administrator;
  message: string;
};

export type ApiErrorPayload = {
  code: string;
  message: string;
  details: unknown;
};

