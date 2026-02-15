"use client";

import type {TodoListItem, PaginatedResponse} from "@/types/todo";
import {TodoCard} from "./todo-card";
import {Skeleton} from "@/components/ui/skeleton";

interface TodoListProps {
    data: PaginatedResponse<TodoListItem> | undefined;
    isLoading: boolean;
    onEdit: (todo: TodoListItem) => void;
    onDelete: (todo: TodoListItem) => void;
}

export function TodoList({data, isLoading, onEdit, onDelete}: TodoListProps) {
    if (isLoading) {
        return (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                {Array.from({length: 6}).map((_, i) => (
                    <Skeleton key={i} className="h-40"/>
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
        <section aria-label="Todo list" aria-live="polite">
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
        </section>
    );
}