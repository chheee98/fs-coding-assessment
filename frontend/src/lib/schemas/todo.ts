import { z } from 'zod';
import { Priority } from '@/types/todo';

export const todoCreateSchema = z.object({
  title: z
    .string()
    .min(1, 'Title is required')
    .max(200, 'Title must be 200 characters or less'),
  description: z
    .string()
    .max(1000, 'Description must be 1000 characters or less')
    .optional(),
  priority: z.nativeEnum(Priority).optional(),
});

export const todoUpdateSchema = z.object({
  title: z
    .string()
    .min(1, 'Title is required')
    .max(200, 'Title must be 200 characters or less')
    .optional(),
  description: z
    .string()
    .max(1000, 'Description must be 1000 characters or less')
    .optional(),
  priority: z.nativeEnum(Priority).optional(),
});

export type TodoCreateFormData = z.infer<typeof todoCreateSchema>;
export type TodoUpdateFormData = z.infer<typeof todoUpdateSchema>;
