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