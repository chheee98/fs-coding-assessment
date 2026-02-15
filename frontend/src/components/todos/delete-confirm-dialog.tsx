"use client";

import {useMutation, useQueryClient} from "@tanstack/react-query";
import {todosApi} from "@/lib/api/todos";
import type {PaginatedResponse, TodoListItem} from "@/types/todo";
import {toast} from "sonner";
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
        onMutate: async () => {
            await queryClient.cancelQueries({queryKey: ["todos"]});

            const previousData = queryClient.getQueriesData<PaginatedResponse<TodoListItem>>({
                queryKey: ["todos"],
            });

            // Remove from cache immediately
            queryClient.setQueriesData<PaginatedResponse<TodoListItem>>(
                {queryKey: ["todos"]},
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
            return {previousData};
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
            queryClient.invalidateQueries({queryKey: ["todos"]});
            queryClient.invalidateQueries({queryKey: ["todoStats"]});
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