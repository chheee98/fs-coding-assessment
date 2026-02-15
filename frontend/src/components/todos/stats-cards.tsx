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
    <section aria-label="Todo statistics" aria-live="polite">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {cards.map((card) => (
          <Card key={card.title}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {card.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold" aria-label={`${card.title}: ${card.value}`}>
                {card.value}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}