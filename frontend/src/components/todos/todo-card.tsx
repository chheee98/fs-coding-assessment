'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { todosApi } from '@/lib/api/todos';
import { useAuth } from '@/hooks/use-auth';
import type { TodoListItem, PaginatedResponse } from '@/types/todo';
import { TodoStatus, Priority } from '@/types/todo';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

const priorityColors: Record<Priority, string> = {
  [Priority.HIGH]: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  [Priority.MEDIUM]:
    'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  [Priority.LOW]:
    'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
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
      await queryClient.cancelQueries({ queryKey: ['todos'] });

      // Snapshot previous data
      const previousData = queryClient.getQueriesData<
        PaginatedResponse<TodoListItem>
      >({
        queryKey: ['todos'],
      });

      // Optimistically update the todo's status in cache
      queryClient.setQueriesData<PaginatedResponse<TodoListItem>>(
        { queryKey: ['todos'] },
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
      toast.error('Failed to update todo status');
    },
    onSuccess: (data) => {
      toast.success(data.status === 'COMPLETED' ? 'Todo completed' : 'Todo uncompleted');
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
      queryClient.invalidateQueries({ queryKey: ['todoStats'] });
    },
  });

  const isPending = toggleMutation.isPending;

  return (
    <Card className={isPending ? 'opacity-60 transition-opacity' : ''}>
      <article aria-label={`Todo: ${todo.title}`}>
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
                  todo.status === TodoStatus.COMPLETED ? 'default' : 'outline'
                }
              >
                {todo.status.replace('_', ' ')}
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
                  ? 'Uncomplete'
                  : 'Complete'}
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
      </article>
    </Card>
  );
}
