'use client';

import {useAuth} from '@/hooks/use-auth';
import {Button} from '@/components/ui/button';

export function Header() {
    const {user, logout} = useAuth();

    return (
        <header className="border-b bg-background">
            <div className="container mx-auto flex h-16 items-center justify-between gap-4 px-4">
                <h1 className="truncate text-xl font-bold">Todo App</h1>
                <nav aria-label="User navigation" className="flex shrink-0 items-center gap-2 sm:gap-4">
                    <span className="hidden text-sm text-muted-foreground sm:inline" aria-label={`Logged in as ${user?.username}`}>
                        {user?.username}
                    </span>
                    <Button variant="outline" size="sm" onClick={logout} aria-label="Logout">
                        Logout
                    </Button>
                </nav>
            </div>
        </header>
    );
}
