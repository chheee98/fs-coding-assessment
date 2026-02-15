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