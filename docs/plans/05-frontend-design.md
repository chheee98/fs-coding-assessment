# 05 — Frontend Design (All Tasks)

## Quick Context

Full frontend design for the TODO application covering all 5 assessment tasks:
Auth, Todo Management, Optimistic Updates & Error Handling, Accessibility, and Responsive Design.

**Backend is complete** — 6 CRUD endpoints, stats, JWT auth, 50+ tests passing.
Frontend is a blank Next.js 15 + Tailwind 4 boilerplate.

## Tech Stack

| Concern | Choice | Why |
|---------|--------|-----|
| UI components | shadcn/ui (Radix + Tailwind) | Accessible out of the box, beautiful defaults |
| HTTP client | axios | Interceptors for auto-token + 401 handling |
| Server state | TanStack React Query | Caching, loading states, optimistic updates in ~5 lines |
| Auth state | Context API | Simple, just stores user/token |
| Token storage | localStorage | Simple, fine for assessment scope |
| Forms | React Hook Form + Zod | Validation with minimal boilerplate, integrates with shadcn |
| Toasts | Sonner (shadcn) | Included with shadcn, accessible |
| Pagination | Page controls (prev/next) | Matches backend's page-based API |
| Create/Edit UI | Modal dialog | Standard, good accessibility (focus trap, Escape) |

## New Libraries

- `@tanstack/react-query` — server state management
- `axios` — HTTP client
- `react-hook-form` — form state management
- `@hookform/resolvers` — Zod integration for RHF
- `zod` — schema validation
- shadcn/ui components (installed via `npx shadcn@latest add ...`)

## Project Structure

```
src/
  app/
    layout.tsx                 # Root layout (QueryProvider, AuthProvider, Sonner)
    page.tsx                   # Redirects to /todos or /login
    (auth)/
      login/page.tsx           # Login page
      register/page.tsx        # Register page
    (dashboard)/
      layout.tsx               # Protected layout (Header with user info + logout)
      todos/page.tsx           # Todo list (filters, search, pagination)

  components/
    ui/                        # shadcn/ui generated components
    auth/
      login-form.tsx
      register-form.tsx
    todos/
      todo-card.tsx            # Single todo item (priority badge, actions)
      todo-list.tsx            # Grid/list of todo cards
      todo-modal.tsx           # Create/edit modal
      todo-filters.tsx         # Priority filter + search bar
      delete-confirm-dialog.tsx
      pagination.tsx
      stats-cards.tsx          # Stats dashboard (total, completed, pending)
    layout/
      header.tsx               # Logo, username, logout button

  lib/
    api/
      client.ts                # axios instance + interceptors (auto-token, 401 redirect)
      auth.ts                  # login(), register() API calls
      todos.ts                 # CRUD + stats + toggle API calls
    schemas/
      auth.ts                  # Zod: loginSchema, registerSchema + inferred types
      todo.ts                  # Zod: todoCreateSchema, todoUpdateSchema + inferred types

  hooks/
    use-auth.ts                # useAuth() hook (wraps AuthContext)
    use-debounce.ts            # Debounced search input

  providers/
    auth-provider.tsx          # AuthContext + Provider (user, token, login, logout)
    query-provider.tsx         # TanStack QueryClientProvider

  types/
    auth.ts                    # AuthToken, User (API responses only)
    todo.ts                    # Todo, TodoListItem, TodoStats, PaginatedResponse (API responses only)
```

## Section 1: Authentication Flow

```
User opens app → AuthProvider checks localStorage for token
  ├─ Token exists → decode it, set user state, show dashboard
  └─ No token → redirect to /login

Login/Register → API call → store token in localStorage → set user in context → redirect to /todos

Any API call returns 401 → axios interceptor clears token → redirect to /login

Logout button → clear localStorage → clear context → redirect to /login
```

**AuthProvider state:**

```ts
type AuthState = {
  user: { id: string; username: string } | null;
  token: string | null;
  isLoading: boolean;  // true while checking localStorage on first load
};
```

**AuthContext exposes:**

```ts
type AuthContext = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username, password) => Promise<void>;
  register: (username, password) => Promise<void>;
  logout: () => void;
};
```

**axios interceptors** (configured once in `lib/api/client.ts`):
- Request interceptor: read token from localStorage → add `Authorization: Bearer <token>` header
- Response interceptor: if 401 → clear localStorage → redirect to `/login`

**Route protection** — `(dashboard)/layout.tsx` checks `isAuthenticated`:
- Still loading → spinner
- Not authenticated → redirect to `/login`
- Authenticated → render children

**Token expiry**: Let the 401 interceptor handle it. When token expires, next API call fails → user redirected to login. Simple and reliable.

## Section 2: Todo Management & Data Flow

**Main page layout (`/todos`):**

```
┌─────────────────────────────────────────────┐
│  Header: [App Name]     [username] [Logout] │
├─────────────────────────────────────────────┤
│  Stats Cards: Total | Completed | Pending   │
├─────────────────────────────────────────────┤
│  [Search bar]  [Priority filter]  [+ New]   │
├─────────────────────────────────────────────┤
│  Todo Card (title, priority badge, actions) │
│  Todo Card (description hidden if not owner)│
│  Todo Card ...                              │
├─────────────────────────────────────────────┤
│  Pagination: [< Prev] 1 2 3 [Next >]       │
└─────────────────────────────────────────────┘
```

**Data flow with React Query:**

```
URL query params (?page=1&priority=HIGH&search=milk)
       ↓
  useQuery(['todos', { page, priority, search }])
       ↓
  todoApi.getAll(params)  →  axios GET /api/v1/todos?page=1&priority=HIGH&search=milk
       ↓
  React Query caches result, provides { data, isLoading, error }
       ↓
  Components render from cache
```

Filters and search update URL query params → React Query sees queryKey change → auto refetches.

**Search**: Debounced 300ms, minimum 2 characters.

**Todo Card behavior by ownership:**

| Feature | Owner | Non-owner |
|---------|-------|-----------|
| Title | Visible | Visible |
| Description | Visible | Hidden (null from API) |
| Priority badge | Visible | Visible |
| Complete toggle | Clickable | Hidden |
| Edit button | Visible | Hidden |
| Delete button | Visible | Hidden |

**CRUD operations:**

| Action | Trigger | API Call | Optimistic Update |
|--------|---------|----------|-------------------|
| Create | Modal submit | POST /todos | Add to cache, refetch |
| Edit | Modal submit | PATCH /todos/:id | Update in cache, rollback on error |
| Delete | Confirm dialog | DELETE /todos/:id | Remove from cache, rollback on error |
| Toggle complete | Click checkbox | PATCH /todos/:id/complete | Toggle in cache, rollback on error |
| View detail | Click todo card | GET /todos/:id | Read only |

**Stats**: Separate `useQuery(['stats'])`, invalidated after any mutation.

## Section 3: Optimistic Updates & Error Handling

**Optimistic update pattern (all mutations):**

```
User action (e.g., click "Complete")
  ├─ 1. Immediately update React Query cache (UI updates instantly)
  ├─ 2. Send API request in background
  ├─ 3a. Success → invalidate queries (refetch fresh data)
  └─ 3b. Failure → rollback cache to previous state + error toast
```

**Visual pending state**: Affected todo card gets `opacity-60` while API call is in flight.

**Error handling — 3 layers:**

| Layer | Catches | Response |
|-------|---------|----------|
| axios interceptor | 401 (expired token) | Clear auth, redirect to `/login` |
| React Query `onError` | API errors (403, 404, 422, 500) | Rollback optimistic update + error toast |
| React Error Boundary | Unexpected React crashes | Fallback UI: "Something went wrong" + retry button |

**Toast notifications (Sonner):**

| Event | Type | Example |
|-------|------|---------|
| Todo created | Success | "Todo created successfully" |
| Todo deleted | Success | "Todo deleted" |
| API error | Error | "Failed to update todo. Please try again." |
| 403 Forbidden | Error | "You don't have permission to do that" |
| Network error | Error | "Network error. Check your connection." |

**Form validation errors**: Displayed inline under each field via React Hook Form + Zod (not as toasts).

**Retry**: React Query's built-in retry (3 attempts, exponential backoff) for failed queries. No custom retry UI needed.

## Section 4: Accessibility

**Free from shadcn/ui (Radix):**
- Modal: focus trap, Escape to close, focus returns to trigger
- Dialog: `role="dialog"`, `aria-labelledby`, `aria-describedby`
- Buttons: keyboard activation (Enter/Space)

**Added manually:**

| Element | Accessibility |
|---------|--------------|
| Todo card actions | `aria-label="Complete todo: Buy milk"` |
| Priority badges | `aria-label="Priority: HIGH"` |
| Search input | `aria-label="Search todos by title"` |
| Filter dropdown | `aria-label="Filter by priority"` |
| Pagination | `<nav aria-label="Pagination">`, `aria-current="page"` |
| Loading states | `aria-live="polite"` region |
| Form errors | `aria-invalid="true"` + `aria-describedby` |

**Keyboard flow**: Tab: Search → Filter → New Todo → Todo cards → Pagination. Escape closes modals.

**Semantic HTML**: `<header>`, `<main>`, `<nav>`, `<article>` for todo cards, `<form>` for forms.

## Section 5: Responsive Design

Mobile-first with Tailwind breakpoints:

```
Mobile (default)          Tablet (md: 768px+)       Desktop (lg: 1024px+)
┌───────────────┐         ┌──────────────────┐      ┌────────────────────────┐
│ Header        │         │ Header           │      │ Header                 │
├───────────────┤         ├──────────────────┤      ├────────────────────────┤
│ Stats (stack) │         │ Stats (row of 3) │      │ Stats (row of 3)       │
├───────────────┤         ├──────────────────┤      ├────────────────────────┤
│ Search        │         │ Search | Filter  │      │ Search | Filter | +New │
│ Filter        │         │ [+ New]          │      ├────────────────────────┤
│ [+ New]       │         ├──────────────────┤      │ Todo  │ Todo  │ Todo   │
├───────────────┤         │ Todo │ Todo      │      │ Todo  │ Todo  │ Todo   │
│ Todo (full w) │         │ Todo │ Todo      │      ├────────────────────────┤
│ Todo (full w) │         ├──────────────────┤      │ Pagination             │
├───────────────┤         │ Pagination       │      └────────────────────────┘
│ Pagination    │         └──────────────────┘
└───────────────┘
```

| Element | Mobile | Tablet | Desktop |
|---------|--------|--------|---------|
| Stats cards | Stacked | Row of 3 | Row of 3 |
| Search + Filter | Stacked | Side by side | Inline with + New |
| Todo grid | 1 column | 2 columns | 3 columns |
| Modal | Full screen | Centered overlay | Centered overlay |
