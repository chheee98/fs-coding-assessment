import { z } from 'zod';

export const loginSchema = z.object({
  username: z.string().min(1, 'Username is required').max(255),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .max(128),
});

export const registerSchema = z.object({
  username: z.string().min(1, 'Username is required').max(255),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .max(128),
  email: z
    .string()
    .email('Invalid email address')
    .max(255)
    .optional()
    .or(z.literal('')),
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
