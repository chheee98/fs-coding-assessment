# Frontend Decisions & Trade-offs

> **Transparency note:** This project was implemented with the assistance of [Claude Code](https://claude.com/claude-code), Anthropic's local AI coding agent. Each decision below was discussed with the AI, where it presented options, trade-offs, and community patterns. The developer (me) made the final call on every decision after understanding the reasoning. This document recaps those decisions from our conversation history.

---

## 1. Feature-Based Project Structure

**Decision:** Organize frontend code by feature (`components/auth/`, `components/todos/`, `components/layout/`) rather than domain modules or flat co-location.

**Discussion:** Three approaches were proposed — feature-based, domain-driven modules, and flat co-location. Feature-based was chosen.

**Why:** Clean separation between pages (routing) and components (UI). Feature folders group related components. Demonstrates strong architecture skills for the assessment. Scales naturally.

**Trade-off:** More directories than flat co-location. But prevents a messy flat `components/` folder as the app grows.

```
src/
  app/                          # Next.js App Router — pages and layouts only
    (auth)/                     #   Public routes (login, register)
    (dashboard)/                #   Protected routes (todos)

  components/
    ui/                         # shadcn/ui generated components
    auth/                       # Login/register forms
    todos/                      # Todo cards, list, modal, filters, pagination, stats
    layout/                     # Header

  lib/
    api/                        # axios client + API functions (auth, todos)
    schemas/                    # Zod schemas + inferred types (single source of truth)

  hooks/                        # Custom hooks (useAuth, useDebounce)
  providers/                    # Context providers (auth, React Query)
  types/                        # API response types only (no form input types)
```

## 2. shadcn/ui (Not Pure Tailwind, Not Headless UI)

**Decision:** Use shadcn/ui for UI components.

**Why:** Built on Radix UI — accessible out of the box (focus traps, keyboard navigation, ARIA attributes). You own the component files (copy-paste, not npm dependency). Beautiful defaults with Tailwind styling.

**Trade-off:** Adds Radix as a dependency. But gains modal focus traps, Escape-to-close, accessible Select/Dialog/AlertDialog for free — features that would take significant effort to build from scratch.

## 3. localStorage for JWT Tokens

**Decision:** Store JWT in localStorage, not httpOnly cookies.

**Discussion:** The frontend README lists both as options. httpOnly cookies are more secure (XSS-immune) but require a backend proxy/BFF layer since the API returns tokens in JSON. Too complex for assessment scope.

**Why:** Simpler implementation. The assessment accepts it as a valid option.

**Trade-off:** Vulnerable to XSS — if an XSS attack succeeds, the token can be stolen. Acceptable for a demo/assessment app. In production, httpOnly cookies would be the better choice.

## 4. axios with Interceptors for Auto-Token

**Decision:** Use axios with request/response interceptors instead of native `fetch`.

**Why:**
- Request interceptor reads JWT from localStorage and attaches `Authorization: Bearer <token>` to every request automatically — no manual header management per API call.
- Response interceptor catches 401 → clears auth state → redirects to `/login`. Handles token expiry globally.

**Trade-off:** `window.location.href` is used for 401 redirect (hard navigation) instead of `router.push()`. The interceptor runs outside React's component tree, so hooks are unavailable. Hard redirect is acceptable for session expiry.

## 5. TanStack React Query for Server State

**Decision:** Use React Query for all API data (todos, stats), Context API only for auth state.

**Discussion:** Developer asked why React Query is needed when axios already handles fetching. AI explained the two layers: axios = makes requests, React Query = manages the results (caching, loading states, refetching, optimistic updates).

**Why:** Without React Query, every component needs manual `useState` + `useEffect` + error/loading state. Optimistic updates (required by assessment) require manual cache management and rollback. React Query handles all of this in ~5 lines per query.

**Trade-off:** Extra dependency. But the assessment requires optimistic updates and error handling — React Query makes that 10x less code than building it manually.

## 6. Zod as Single Source of Truth (No Duplicate Types)

**Decision:** Form input types are defined once in Zod schemas (`lib/schemas/`) and inferred via `z.infer`. No separate TypeScript interfaces for form inputs in `types/`.

**Discussion:** The initial plan had both `types/auth.ts` (`LoginCredentials`) and `validations/auth.ts` (`loginSchema` + `LoginFormData`) — duplicating the same fields. The developer flagged this as bad practice that leads to sync drift and missing fields. AI researched community patterns.

**Research findings:** The entire React/TypeScript community has moved to "Zod as single source of truth" — confirmed by Zod's official docs, T3 stack, tRPC, Cal.com, and expert consensus (2025-2026). No major project maintains separate type files alongside Zod schemas.

**Why:** Change once, type updates automatically. No sync drift, no missing fields. Less code. Runtime + compile-time safety from one definition.

**Result:**
- `lib/schemas/auth.ts` — Zod schemas + inferred types (form inputs, used everywhere)
- `types/auth.ts` — API response types only (`AuthToken`, `User` — not validated in forms)

**Trade-off:** Vendor lock-in to Zod. Mitigated by the Standard Schema initiative (Zod v4, Valibot, ArkType all support it). IDE hover shows `z.infer<typeof Schema>` instead of a named interface — functionally equivalent.

## 7. `schemas/` Instead of `validations/`

**Decision:** Rename `lib/validations/` to `lib/schemas/` to match community convention.

**Why:** The Zod community organizes files as "schemas" (the thing you define) rather than "validations" (what they do). This aligns with Zod's documentation, T3 stack, and most open-source Next.js projects.

## 8. React Hook Form + Zod for Forms

**Decision:** Use React Hook Form (RHF) for form state management, integrated with Zod for validation.

**Discussion:** Developer asked what RHF does. It manages form values, error states, dirty/touched tracking, and submission state — replacing 2x `useState` per field + manual validation logic.

**Why:** Without RHF, every form needs `useState` per field, manual error tracking, manual `isSubmitting` state, manual dirty state detection. With 4 forms (login, register, create todo, edit todo), that's a lot of repetitive boilerplate.

**Trade-off:** Learning curve for RHF's `render` prop pattern. But shadcn/ui has built-in `Form` components that integrate with RHF, reducing the boilerplate further.
