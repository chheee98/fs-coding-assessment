import { api } from './client';
import type {
  Todo,
  TodoListItem,
  TodoStats,
  PaginatedResponse,
} from '@/types/todo';
import type {
  TodoCreateFormData,
  TodoUpdateFormData,
} from '@/lib/schemas/todo';

export interface TodoListParams {
  page?: number;
  page_size?: number;
  priority?: string;
  completed?: boolean;
  search?: string;
}

export const todosApi = {
  getAll: async (
    params: TodoListParams = {}
  ): Promise<PaginatedResponse<TodoListItem>> => {
    const { data } = await api.get<PaginatedResponse<TodoListItem>>('/todos', {
      params,
    });
    return data;
  },

  getById: async (id: string): Promise<Todo> => {
    const { data } = await api.get<Todo>(`/todos/${id}`);
    return data;
  },

  create: async (todo: TodoCreateFormData): Promise<Todo> => {
    const { data } = await api.post<Todo>('/todos', todo);
    return data;
  },

  update: async (id: string, todo: TodoUpdateFormData): Promise<Todo> => {
    const { data } = await api.patch<Todo>(`/todos/${id}`, todo);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/todos/${id}`);
  },

  toggleComplete: async (id: string): Promise<Todo> => {
    const { data } = await api.patch<Todo>(`/todos/${id}/complete`);
    return data;
  },

  getStats: async (): Promise<TodoStats> => {
    const { data } = await api.get<TodoStats>('/todos/stats');
    return data;
  },
};
