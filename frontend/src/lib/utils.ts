import { clsx, type ClassValue } from 'clsx';
import type { FieldValues, UseFormReturn } from 'react-hook-form';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Extract only the fields that were changed from a React Hook Form submission. */
export function getDirtyValues<T extends FieldValues>(
  form: UseFormReturn<T>,
  data: T
): Partial<T> {
  const dirtyFields = form.formState.dirtyFields;
  const result: Partial<T> = {};
  for (const key of Object.keys(dirtyFields) as (keyof T)[]) {
    result[key] = data[key];
  }
  return result;
}
