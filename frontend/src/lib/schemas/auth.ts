import { z } from 'zod';

const usernameField = z
  .string()
  .min(3, 'Username must be at least 3 characters')
  .max(255)
  .regex(
    /^[a-zA-Z0-9_-]+$/,
    'Only letters, numbers, underscores, and hyphens allowed'
  );

const passwordField = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .max(128)
  .regex(
    /^[a-zA-Z0-9!@#$%^&*(),.?":{}|<>_\-]+$/,
    'Only letters, numbers, and special characters allowed'
  );

export const loginSchema = z.object({
  username: usernameField,
  password: passwordField,
});

export const registerSchema = z.object({
  username: usernameField,
  password: passwordField,
  email: z
    .string()
    .email('Invalid email address')
    .max(255)
    .optional()
    .or(z.literal('')),
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
