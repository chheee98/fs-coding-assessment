# Frontend Task 3: Optimistic Updates & Error Handling

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add optimistic updates to all mutations (instant UI feedback), global error handling (error boundary + 401 interceptor), and toast notifications for all user actions.

**Architecture:** React Query's `onMutate`/`onError`/`onSettled` for optimistic cache updates. React Error Boundary for unexpected crashes. Sonner toasts for user feedback.

**Tech Stack:** TanStack React Query (mutation hooks), Sonner (toasts), React (Error Boundary)

---

## Quick Context

This task upgrades the mutations from Task 2 to use optimistic updates — the UI updates instantly before the API responds, and rolls back if the request fails. Also adds a global error boundary for unexpected React crashes.

**Depends on:** Task 2 (mutations already exist, this task enhances them)
**Blocks:** Nothing

## New Libraries

None — all dependencies were installed in Task 1.

## Project Structure (Before → After)

```
frontend/src/
  + components/
      + error-boundary.tsx              # Global React error boundary
  ~ components/todos/
      ~ todo-card.tsx                   # Add optimistic toggle + pending state
      ~ delete-confirm-dialog.tsx       # Add optimistic delete
      ~ todo-modal.tsx                  # Add optimistic create/update
  ~ app/
      ~ layout.tsx                      # Wrap with ErrorBoundary
```

Legend: `+` added, `~` modified

## Acceptance Criteria

- [ ] Toggle complete updates UI instantly (status flips before API responds)
- [ ] Delete removes card from list instantly before API responds
- [ ] Create/update show in list immediately
- [ ] If API fails: UI rolls back to previous state + error toast shown
- [ ] Pending state: affected todo card shows reduced opacity while syncing
- [ ] Error boundary catches unexpected React errors and shows fallback UI
- [ ] Error boundary has "Try Again" button to recover
- [ ] All success/error actions show toast notifications

---

## Implementation

### Step 1: Create `src/components/error-boundary.tsx`

Catches unexpected React rendering errors. Class component required (React limitation).

```tsx
"use client";

import React from "react";
import { Button } from "@/components/ui/button";

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4">
          <h2 className="text-xl font-bold">Something went wrong</h2>
          <p className="text-muted-foreground">
            An unexpected error occurred. Please try again.
          </p>
          <Button onClick={() => this.setState({ hasError: false })}>
            Try Again
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Step 2: Update `src/app/layout.tsx`

Wrap children with ErrorBoundary.

```tsx
// Add import at top:
import { ErrorBoundary } from "@/components/error-boundary";

// Wrap inside body:
<body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
  <ErrorBoundary>
    <QueryProvider>
      <AuthProvider>
        {children}
        <Toaster />
      </AuthProvider>
    </QueryProvider>
  </ErrorBoundary>
</body>
```

### Step 3: Update `src/components/todos/todo-card.tsx`

Add optimistic toggle and visual pending state.

**Changes:**
- `toggleMutation` gets `onMutate` (optimistic cache update) and `onError` (rollback)
- Card gets `opacity-60` class when any mutation is pending

```tsx
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { todosApi } from "@/lib/api/todos";
import { useAuth } from "@/hooks/use-auth";
import type { TodoListItem, PaginatedResponse } from "@/types/todo";
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
    onMutate: async () => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["todos"] });

      // Snapshot previous data
      const previousData = queryClient.getQueriesData<PaginatedResponse<TodoListItem>>({
        queryKey: ["todos"],
      });

      // Optimistically update the todo's status in cache
      queryClient.setQueriesData<PaginatedResponse<TodoListItem>>(
        { queryKey: ["todos"] },
        (old) => {
          if (!old) return old;
          return {
            ...old,
            items: old.items.map((t) =>
              t.id === todo.id
                ? {
                    ...t,
                    status:
                      t.status === TodoStatus.COMPLETED
                        ? TodoStatus.NOT_STARTED
                        : TodoStatus.COMPLETED,
                  }
                : t
            ),
          };
        }
      );

      return { previousData };
    },
    onError: (_err, _vars, context) => {
      // Rollback on error
      if (context?.previousData) {
        for (const [queryKey, data] of context.previousData) {
          queryClient.setQueryData(queryKey, data);
        }
      }
      toast.error("Failed to update todo status");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      queryClient.invalidateQueries({ queryKey: ["todoStats"] });
    },
  });

  const isPending = toggleMutation.isPending;

  return (
    <Card className={isPending ? "opacity-60 transition-opacity" : ""}>
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
              disabled={isPending}
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
            >
              Edit
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => onDelete(todo)}
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

**What changed from Task 2 version:**
- `toggleMutation` now has `onMutate` (optimistic update), `onError` (rollback), `onSettled` (refetch)
- Card root element gets `opacity-60` class when `isPending`
- Success toast removed from `onSuccess` — the UI already updated optimistically. Toast on error only.

### Step 4: Update `src/components/todos/delete-confirm-dialog.tsx`

Add optimistic delete — remove from cache instantly before API responds.

**Changes to `deleteMutation`:**

```typescript
const deleteMutation = useMutation({
  mutationFn: () => todosApi.delete(todo!.id),
  onMutate: async () => {
    await queryClient.cancelQueries({ queryKey: ["todos"] });

    const previousData = queryClient.getQueriesData<PaginatedResponse<TodoListItem>>({
      queryKey: ["todos"],
    });

    // Remove from cache immediately
    queryClient.setQueriesData<PaginatedResponse<TodoListItem>>(
      { queryKey: ["todos"] },
      (old) => {
        if (!old) return old;
        return {
          ...old,
          items: old.items.filter((t) => t.id !== todo!.id),
          total: old.total - 1,
        };
      }
    );

    onOpenChange(false);
    return { previousData };
  },
  onError: (_err, _vars, context) => {
    if (context?.previousData) {
      for (const [queryKey, data] of context.previousData) {
        queryClient.setQueryData(queryKey, data);
      }
    }
    toast.error("Failed to delete todo");
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ["todos"] });
    queryClient.invalidateQueries({ queryKey: ["todoStats"] });
  },
});
```

**Note:** Add `import type { PaginatedResponse, TodoListItem } from "@/types/todo"` at top.

### Step 5: Update `src/components/todos/todo-modal.tsx`

For **create**: no optimistic update needed (we don't have the server-generated ID yet). Just invalidate on success.

For **edit**: optimistic update in cache + rollback on error.

**Changes to `updateMutation`:**

```typescript
const updateMutation = useMutation({
  mutationFn: (data: TodoCreateFormData) =>
    todosApi.update(editingTodo!.id, data),
  onMutate: async (data) => {
    await queryClient.cancelQueries({ queryKey: ["todos"] });

    const previousData = queryClient.getQueriesData<PaginatedResponse<TodoListItem>>({
      queryKey: ["todos"],
    });

    // Optimistically update in cache
    queryClient.setQueriesData<PaginatedResponse<TodoListItem>>(
      { queryKey: ["todos"] },
      (old) => {
        if (!old) return old;
        return {
          ...old,
          items: old.items.map((t) =>
            t.id === editingTodo!.id ? { ...t, ...data } : t
          ),
        };
      }
    );

    onOpenChange(false);
    return { previousData };
  },
  onError: (_err, _vars, context) => {
    if (context?.previousData) {
      for (const [queryKey, data] of context.previousData) {
        queryClient.setQueryData(queryKey, data);
      }
    }
    toast.error("Failed to update todo");
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ["todos"] });
    queryClient.invalidateQueries({ queryKey: ["todoStats"] });
  },
});
```

**Note:** Add `import type { PaginatedResponse, TodoListItem } from "@/types/todo"` at top.

The `createMutation` stays mostly the same — just `invalidateQueries` on success (no optimistic update since we need server-generated ID/timestamps).

### Step 6: Verify

1. Toggle a todo → status badge flips instantly (before network responds)
2. Throttle network in DevTools (slow 3G) → see the instant update + opacity
3. Delete a todo → card disappears instantly
4. Edit a todo → changes reflect instantly
5. Disconnect network → toggle a todo → error toast appears, UI rolls back
6. Trigger a React error (e.g., temporarily throw in a component) → error boundary shows with "Try Again" button
