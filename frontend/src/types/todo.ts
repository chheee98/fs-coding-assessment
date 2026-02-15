export enum Priority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
}

export enum TodoStatus {
  NOT_STARTED = 'NOT_STARTED',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
}

export interface Todo {
  id: string;
  title: string;
  description: string;
  status: TodoStatus;
  priority: Priority | null;
  due_date: string | null;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface TodoListItem {
  id: string;
  title: string;
  description: string | null;
  status: TodoStatus;
  priority: Priority | null;
  due_date: string | null;
  user_id: string;
  created_at: string;
  updated_at: string;
}

// TodoCreate and TodoUpdate removed — inferred from Zod schemas in lib/schemas/todo.ts

export interface TodoStats {
  total: number;
  completed: number;
  pending: number;
  by_priority: {
    LOW: number;
    MEDIUM: number;
    HIGH: number;
  };
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
