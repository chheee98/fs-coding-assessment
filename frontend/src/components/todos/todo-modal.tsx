"use client";

import {useEffect} from "react";
import {useForm} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";
import {useMutation, useQueryClient} from "@tanstack/react-query";
import {AxiosError} from "axios";
import {todosApi} from "@/lib/api/todos";
import {todoCreateSchema, type TodoCreateFormData} from "@/lib/schemas/todo";
import {PaginatedResponse, Priority, type TodoListItem} from "@/types/todo";
import {toast} from "sonner";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogDescription,
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
import {Input} from "@/components/ui/input";
import {Textarea} from "@/components/ui/textarea";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {Button} from "@/components/ui/button";

interface TodoModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    editingTodo?: TodoListItem | null;
}

export function TodoModal({open, onOpenChange, editingTodo}: TodoModalProps) {
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
            form.reset({title: "", description: "", priority: undefined});
        }
    }, [editingTodo, form]);

    const createMutation = useMutation({
        mutationFn: todosApi.create,
        onSuccess: () => {
            queryClient.invalidateQueries({queryKey: ["todos"]});
            queryClient.invalidateQueries({queryKey: ["todoStats"]});
            toast.success("Todo created successfully");
            form.reset({title: "", description: "", priority: undefined});
            onOpenChange(false);
        },
        onError: (error: AxiosError<{ detail?: string }>) => {
            toast.error(error.response?.data?.detail || "Failed to create todo");
        },
    });

    const updateMutation = useMutation({
        mutationFn: (data: TodoCreateFormData) =>
            todosApi.update(editingTodo!.id, data),
        onMutate: async (data) => {
            await queryClient.cancelQueries({queryKey: ["todos"]});

            const previousData = queryClient.getQueriesData<PaginatedResponse<TodoListItem>>({
                queryKey: ["todos"],
            });

            // Optimistically update in cache
            queryClient.setQueriesData<PaginatedResponse<TodoListItem>>(
                {queryKey: ["todos"]},
                (old) => {
                    if (!old) return old;
                    return {
                        ...old,
                        items: old.items.map((t) =>
                            t.id === editingTodo!.id ? {...t, ...data} : t
                        ),
                    };
                }
            );

            return {previousData};
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
            queryClient.invalidateQueries({queryKey: ["todos"]});
            queryClient.invalidateQueries({queryKey: ["todoStats"]});
            onOpenChange(false);
        },
    });

    const onSubmit = (data: TodoCreateFormData) => {
        // Clean up empty optional fields
        const payload: TodoCreateFormData = {title: data.title};
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
                            render={({field}) => (
                                <FormItem>
                                    <FormLabel>Title</FormLabel>
                                    <FormControl>
                                        <Input
                                            placeholder="What needs to be done?"
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormMessage/>
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="description"
                            render={({field}) => (
                                <FormItem>
                                    <FormLabel>Description</FormLabel>
                                    <FormControl>
                                        <Textarea
                                            placeholder="Add more details..."
                                            rows={3}
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormMessage/>
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="priority"
                            render={({field}) => (
                                <FormItem>
                                    <FormLabel>Priority</FormLabel>
                                    <Select
                                        onValueChange={field.onChange}
                                        value={field.value ?? ""}
                                    >
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select priority"/>
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
                                    <FormMessage/>
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