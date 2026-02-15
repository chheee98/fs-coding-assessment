# Frontend Task 2: Todo Management

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the complete todo management interface — list view with pagination/filtering/search, create/edit modals, delete confirmation, and toggle complete.

**Architecture:** React Query for server state (fetching, caching, mutations), URL query params for filter state (shareable URLs), modals for create/edit, optimistic-ready mutation structure.

**Tech Stack:** TanStack React Query, React Hook Form, Zod, shadcn/ui, axios

---

## Quick Context

The main feature of the app. After this task, users can view all todos, create/edit/delete their own, filter by priority, search by title, paginate through results, and see stats.

**Depends on:** Task 1 (auth, providers, API client, types all exist)
**Blocks:** Task 3 (optimistic updates build on top of mutations defined here)

## New Libraries

None — all dependencies were installed in Task 1.

## Project Structure (Before → After)

```
frontend/src/
  + lib/
      + api/
          + todos.ts                    # Todo API functions (CRUD + stats + toggle)
      + schemas/
          + todo.ts                     # Zod schemas + inferred types (single source of truth for form inputs)
  + hooks/
      + use-debounce.ts                 # Debounced value hook for search
  + components/
      + todos/
          + stats-cards.tsx             # Stats: total, completed, pending
          + todo-filters.tsx            # Search bar + priority filter
          + todo-list.tsx               # Grid of todo cards
          + todo-card.tsx               # Single todo card with actions
          + todo-modal.tsx              # Create/edit modal with form
          + delete-confirm-dialog.tsx   # Delete confirmation dialog
          + pagination.tsx              # Page controls
  app/
    (dashboard)/
      ~ todos/page.tsx                  # Replace placeholder with full implementation
```

Legend: `+` added, `~` modified

## Acceptance Criteria

### List View
- [ ] Displays all todos with pagination (20 per page)
- [ ] Filtering by priority (HIGH, MEDIUM, LOW)
- [ ] Search by title (debounced 300ms, min 2 chars)
- [ ] Empty state with helpful message
- [ ] Loading spinner during fetch
- [ ] Pagination controls (prev/next + page numbers)

### Todo Card
- [ ] Shows title, priority badge, status
- [ ] Shows description only for owner's todos
- [ ] Complete/uncomplete toggle (owner only)
- [ ] Edit button (owner only)
- [ ] Delete button (owner only)
- [ ] Priority indicated by color badge

### Create/Edit
- [ ] Modal for todo creation
- [ ] Modal for todo editing (pre-filled with current values)
- [ ] Title (required, max 200 chars), description (textarea), priority selector
- [ ] Real-time validation via Zod
- [ ] Submit and cancel actions

### Delete
- [ ] Confirmation dialog before delete
- [ ] Returns to list after successful delete

### Stats
- [ ] Stats cards showing total, completed, pending counts
- [ ] Refreshes after any mutation

---

## Implementation

### Step 1: Create `src/lib/api/todos.ts`

All todo API calls. Used by React Query hooks.

```typescript
import { api } from "./client";
import type {
  Todo,
  TodoListItem,
  TodoStats,
  PaginatedResponse,
} from "@/types/todo";
import type { TodoCreateFormData, TodoUpdateFormData } from "@/lib/schemas/todo";

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
    const { data } = await api.get<PaginatedResponse<TodoListItem>>("/todos", {
      params,
    });
    return data;
  },

  getById: async (id: string): Promise<Todo> => {
    const { data } = await api.get<Todo>(`/todos/${id}`);
    return data;
  },

  create: async (todo: TodoCreateFormData): Promise<Todo> => {
    const { data } = await api.post<Todo>("/todos", todo);
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
    const { data } = await api.get<TodoStats>("/todos/stats");
    return data;
  },
};
```

### Step 2: Create `src/lib/schemas/todo.ts`

Zod schemas as single source of truth for form input types. No separate `TodoCreate`/`TodoUpdate` interfaces needed.

```typescript
import { z } from "zod";
import { Priority } from "@/types/todo";

export const todoCreateSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title must be 200 characters or less"),
  description: z.string().max(1000, "Description must be 1000 characters or less").optional(),
  priority: z.nativeEnum(Priority).optional(),
});

export const todoUpdateSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title must be 200 characters or less").optional(),
  description: z.string().max(1000, "Description must be 1000 characters or less").optional(),
  priority: z.nativeEnum(Priority).optional(),
});

export type TodoCreateFormData = z.infer<typeof todoCreateSchema>;
export type TodoUpdateFormData = z.infer<typeof todoUpdateSchema>;
```

### Step 3: Create `src/hooks/use-debounce.ts`

```typescript
"use client";

import { useEffect, useState } from "react";

export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
```

### Step 4: Create `src/components/todos/stats-cards.tsx`

```tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { todosApi } from "@/lib/api/todos";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function StatsCards() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["todoStats"],
    queryFn: todosApi.getStats,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
    );
  }

  const cards = [
    { title: "Total", value: stats?.total ?? 0 },
    { title: "Completed", value: stats?.completed ?? 0 },
    { title: "Pending", value: stats?.pending ?? 0 },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {card.title}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{card.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
```

### Step 5: Create `src/components/todos/todo-filters.tsx`

Search bar + priority filter + "New Todo" button. Updates URL query params.

```tsx
"use client";

import { useCallback, useState, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Priority } from "@/types/todo";

interface TodoFiltersProps {
  onCreateClick: () => void;
}

export function TodoFilters({ onCreateClick }: TodoFiltersProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const priority = searchParams.get("priority") ?? "";

  // Local state for search input — debounce before pushing to URL
  const [searchInput, setSearchInput] = useState(searchParams.get("search") ?? "");
  const isFirstRender = useRef(true);

  useEffect(() => {
    // Skip the first render to avoid pushing on mount
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    const timer = setTimeout(() => {
      const params = new URLSearchParams(searchParams.toString());
      if (searchInput) {
        params.set("search", searchInput);
      } else {
        params.delete("search");
      }
      params.delete("page");
      router.push(`?${params.toString()}`);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchInput]); // eslint-disable-line react-hooks/exhaustive-deps

  const updateParams = useCallback(
    (key: string, value: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value) {
        params.set(key, value);
      } else {
        params.delete(key);
      }
      // Reset to page 1 when filters change
      params.delete("page");
      router.push(`?${params.toString()}`);
    },
    [router, searchParams]
  );

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
      <Input
        placeholder="Search todos by title..."
        value={searchInput}
        onChange={(e) => setSearchInput(e.target.value)}
        className="sm:max-w-xs"
        aria-label="Search todos by title"
      />
      <Select
        value={priority}
        onValueChange={(value) =>
          updateParams("priority", value === "ALL" ? "" : value)
        }
      >
        <SelectTrigger className="w-full sm:w-40" aria-label="Filter by priority">
          <SelectValue placeholder="All Priorities" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="ALL">All Priorities</SelectItem>
          {Object.values(Priority).map((p) => (
            <SelectItem key={p} value={p}>
              {p}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button onClick={onCreateClick} className="sm:ml-auto">
        + New Todo
      </Button>
    </div>
  );
}
```

**Design note:** Filters are stored in URL search params, not React state. This makes URLs shareable and filter state survives page refresh. React Query's `queryKey` includes these params, so changing them triggers a refetch automatically. Search uses local state with a 300ms debounce before pushing to URL — this prevents firing an API call per keystroke.

### Step 6: Create `src/components/todos/todo-card.tsx`

Displays a single todo with priority badge and owner-only actions.

```tsx
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { todosApi } from "@/lib/api/todos";
import { useAuth } from "@/hooks/use-auth";
import type { TodoListItem } from "@/types/todo";
import { TodoStatus, Priority } from "@/types/todo";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

const priorityColors: Record<Priority, string> = {
  [Priority.HIGH]: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  [Priority.MEDIUM]: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  [Priority.LOW]: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
};

interface TodoCardProps {
  todo: TodoListItem;
  onEdit: (todo: TodoListItem) => void;
  onDelete: (todo: TodoListItem) => void;
}

export function TodoCard({ todo, onEdit, onDelete }: TodoCardProps) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const isOwner = user?.id === todo.user_id;

  const toggleMutation = useMutation({
    mutationFn: () => todosApi.toggleComplete(todo.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      queryClient.invalidateQueries({ queryKey: ["todoStats"] });
      toast.success(
        todo.status === TodoStatus.COMPLETED
          ? "Todo marked as not started"
          : "Todo marked as completed"
      );
    },
    onError: () => {
      toast.error("Failed to update todo status");
    },
  });

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base leading-tight">
            {todo.title}
          </CardTitle>
          <div className="flex shrink-0 items-center gap-1">
            {todo.priority && (
              <Badge
                variant="secondary"
                className={priorityColors[todo.priority]}
                aria-label={`Priority: ${todo.priority}`}
              >
                {todo.priority}
              </Badge>
            )}
            <Badge
              variant={
                todo.status === TodoStatus.COMPLETED ? "default" : "outline"
              }
            >
              {todo.status.replace("_", " ")}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {todo.description !== null && (
          <p className="mb-4 text-sm text-muted-foreground">
            {todo.description}
          </p>
        )}

        {isOwner && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => toggleMutation.mutate()}
              disabled={toggleMutation.isPending}
              aria-label={`Toggle complete: ${todo.title}`}
            >
              {todo.status === TodoStatus.COMPLETED
                ? "Uncomplete"
                : "Complete"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onEdit(todo)}
              aria-label={`Edit: ${todo.title}`}
            >
              Edit
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => onDelete(todo)}
              aria-label={`Delete: ${todo.title}`}
            >
              Delete
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

**Design note:** `description !== null` check — the backend returns `null` for non-owner's descriptions. If null, we don't render the description paragraph at all.

### Step 7: Create `src/components/todos/todo-list.tsx`

Renders the grid of todo cards or empty/loading states.

```tsx
"use client";

import type { TodoListItem, PaginatedResponse } from "@/types/todo";
import { TodoCard } from "./todo-card";
import { Skeleton } from "@/components/ui/skeleton";

interface TodoListProps {
  data: PaginatedResponse<TodoListItem> | undefined;
  isLoading: boolean;
  onEdit: (todo: TodoListItem) => void;
  onDelete: (todo: TodoListItem) => void;
}

export function TodoList({ data, isLoading, onEdit, onDelete }: TodoListProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-40" />
        ))}
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <p className="text-lg font-medium text-muted-foreground">
          No todos found
        </p>
        <p className="text-sm text-muted-foreground">
          Try adjusting your filters or create a new todo.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {data.items.map((todo) => (
        <TodoCard
          key={todo.id}
          todo={todo}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
```

### Step 8: Create `src/components/todos/pagination.tsx`

Page controls with prev/next and page numbers.

```tsx
"use client";

import { useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";

interface PaginationProps {
  page: number;
  totalPages: number;
}

export function Pagination({ page, totalPages }: PaginationProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const goToPage = useCallback(
    (newPage: number) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set("page", String(newPage));
      router.push(`?${params.toString()}`);
    },
    [router, searchParams]
  );

  if (totalPages <= 1) return null;

  // Show up to 5 page numbers centered around current page
  const startPage = Math.max(1, page - 2);
  const endPage = Math.min(totalPages, startPage + 4);

  const pages = Array.from(
    { length: endPage - startPage + 1 },
    (_, i) => startPage + i
  );

  return (
    <nav aria-label="Pagination" className="flex items-center justify-center gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={() => goToPage(page - 1)}
        disabled={page <= 1}
      >
        Previous
      </Button>

      {pages.map((p) => (
        <Button
          key={p}
          variant={p === page ? "default" : "outline"}
          size="sm"
          onClick={() => goToPage(p)}
          aria-current={p === page ? "page" : undefined}
        >
          {p}
        </Button>
      ))}

      <Button
        variant="outline"
        size="sm"
        onClick={() => goToPage(page + 1)}
        disabled={page >= totalPages}
      >
        Next
      </Button>
    </nav>
  );
}
```

### Step 9: Create `src/components/todos/todo-modal.tsx`

Create/edit modal using shadcn Dialog + React Hook Form + Zod.

```tsx
"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { todosApi } from "@/lib/api/todos";
import { todoCreateSchema, type TodoCreateFormData } from "@/lib/schemas/todo";
import { Priority, type TodoListItem } from "@/types/todo";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";

interface TodoModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editingTodo?: TodoListItem | null;
}

export function TodoModal({ open, onOpenChange, editingTodo }: TodoModalProps) {
  const queryClient = useQueryClient();
  const isEditing = !!editingTodo;

  const form = useForm<TodoCreateFormData>({
    resolver: zodResolver(todoCreateSchema),
    defaultValues: {
      title: "",
      description: "",
      priority: undefined,
    },
  });

  // Populate form when editing
  useEffect(() => {
    if (editingTodo) {
      form.reset({
        title: editingTodo.title,
        description: editingTodo.description ?? "",
        priority: editingTodo.priority ?? undefined,
      });
    } else {
      form.reset({ title: "", description: "", priority: undefined });
    }
  }, [editingTodo, form]);

  const createMutation = useMutation({
    mutationFn: todosApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      queryClient.invalidateQueries({ queryKey: ["todoStats"] });
      toast.success("Todo created successfully");
      form.reset({ title: "", description: "", priority: undefined });
      onOpenChange(false);
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      toast.error(error.response?.data?.detail || "Failed to create todo");
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: TodoCreateFormData) =>
      todosApi.update(editingTodo!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      queryClient.invalidateQueries({ queryKey: ["todoStats"] });
      toast.success("Todo updated successfully");
      onOpenChange(false);
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      toast.error(error.response?.data?.detail || "Failed to update todo");
    },
  });

  const onSubmit = (data: TodoCreateFormData) => {
    // Clean up empty optional fields
    const payload: TodoCreateFormData = { title: data.title };
    if (data.description) payload.description = data.description;
    if (data.priority) payload.priority = data.priority;

    if (isEditing) {
      updateMutation.mutate(payload);
    } else {
      createMutation.mutate(payload);
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;
  const isDirty = form.formState.isDirty;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{isEditing ? "Edit Todo" : "Create Todo"}</DialogTitle>
          <DialogDescription>
            {isEditing ? "Update the details of your todo." : "Fill in the details to create a new todo."}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Title</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="What needs to be done?"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Add more details..."
                      rows={3}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="priority"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Priority</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    value={field.value ?? ""}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select priority" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {Object.values(Priority).map((p) => (
                        <SelectItem key={p} value={p}>
                          {p}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isPending || (isEditing && !isDirty)}>
                {isPending
                  ? isEditing
                    ? "Saving..."
                    : "Creating..."
                  : isEditing
                    ? "Save Changes"
                    : "Create Todo"}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
```

### Step 10: Create `src/components/todos/delete-confirm-dialog.tsx`

```tsx
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { todosApi } from "@/lib/api/todos";
import type { TodoListItem } from "@/types/todo";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface DeleteConfirmDialogProps {
  todo: TodoListItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DeleteConfirmDialog({
  todo,
  open,
  onOpenChange,
}: DeleteConfirmDialogProps) {
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: () => todosApi.delete(todo!.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      queryClient.invalidateQueries({ queryKey: ["todoStats"] });
      toast.success("Todo deleted");
      onOpenChange(false);
    },
    onError: () => {
      toast.error("Failed to delete todo");
    },
  });

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Todo</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete &quot;{todo?.title}&quot;? This
            action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => deleteMutation.mutate()}
            disabled={deleteMutation.isPending}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {deleteMutation.isPending ? "Deleting..." : "Delete"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

### Step 11: Update `src/app/(dashboard)/todos/page.tsx`

Wire everything together. This is the main page.

```tsx
"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { todosApi } from "@/lib/api/todos";
import { useDebounce } from "@/hooks/use-debounce";
import type { TodoListItem } from "@/types/todo";
import { StatsCards } from "@/components/todos/stats-cards";
import { TodoFilters } from "@/components/todos/todo-filters";
import { TodoList } from "@/components/todos/todo-list";
import { Pagination } from "@/components/todos/pagination";
import { TodoModal } from "@/components/todos/todo-modal";
import { DeleteConfirmDialog } from "@/components/todos/delete-confirm-dialog";

export default function TodosPage() {
  const searchParams = useSearchParams();

  // Read filter state from URL
  const page = Number(searchParams.get("page") ?? "1");
  const priority = searchParams.get("priority") ?? undefined;
  const search = searchParams.get("search") ?? "";

  // Debounce search with 300ms delay, min 2 chars
  const debouncedSearch = useDebounce(search, 300);
  const effectiveSearch =
    debouncedSearch.length >= 2 ? debouncedSearch : undefined;

  // Fetch todos
  const { data, isLoading } = useQuery({
    queryKey: ["todos", { page, priority, search: effectiveSearch }],
    queryFn: () =>
      todosApi.getAll({
        page,
        page_size: 20,
        priority,
        search: effectiveSearch,
      }),
  });

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTodo, setEditingTodo] = useState<TodoListItem | null>(null);

  // Delete dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingTodo, setDeletingTodo] = useState<TodoListItem | null>(null);

  const handleCreate = () => {
    setEditingTodo(null);
    setModalOpen(true);
  };

  const handleEdit = (todo: TodoListItem) => {
    setEditingTodo(todo);
    setModalOpen(true);
  };

  const handleDelete = (todo: TodoListItem) => {
    setDeletingTodo(todo);
    setDeleteDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      <StatsCards />
      <TodoFilters onCreateClick={handleCreate} />
      <TodoList
        data={data}
        isLoading={isLoading}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />
      {data && (
        <Pagination page={data.page} totalPages={data.total_pages} />
      )}
      <TodoModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        editingTodo={editingTodo}
      />
      <DeleteConfirmDialog
        todo={deletingTodo}
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
      />
    </div>
  );
}
```

### Step 12: Verify

1. Backend running at `localhost:8000`
2. Login → should see the todo dashboard with stats, filters, and empty state
3. Click "+ New Todo" → modal opens, fill in fields, submit → todo appears in list
4. Stats update after creating a todo
5. Click "Edit" on your todo → modal opens pre-filled, save → changes reflected
6. Click "Delete" → confirmation dialog → confirm → todo removed
7. Click "Complete" → status toggles
8. Other users' todos show without description and without action buttons
9. Filter by priority → list filters
10. Type in search → list filters (after 300ms debounce, 2+ chars)
11. Pagination works when you have > 20 todos
12. Run `npm run type-check` → no TypeScript errors
