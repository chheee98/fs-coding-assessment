// API response types only — no form input types here.
// Form input types are inferred from Zod schemas in lib/schemas/auth.ts

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  username: string;
  email: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}
