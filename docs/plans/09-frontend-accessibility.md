# Frontend Task 4: Accessibility & UX

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Audit and enhance accessibility across all components — semantic HTML, ARIA attributes, keyboard navigation, and screen reader support.

**Architecture:** Review all components created in Tasks 1-3 and add missing accessibility features. Most heavy lifting is already done by shadcn/ui (Radix), this task fills the gaps.

**Tech Stack:** HTML5 semantics, WAI-ARIA, shadcn/ui (Radix — already accessible)

---

## Quick Context

Tasks 1-2 already include basic accessibility (ARIA labels on key elements, semantic structure). This task is a focused audit pass to ensure full compliance with the assessment requirements.

**Depends on:** Tasks 1-2 (components must exist to enhance)
**Blocks:** Nothing

## New Libraries

None.

## Project Structure (Before → After)

```
frontend/src/
  ~ components/layout/
      ~ header.tsx                      # Add semantic nav, skip link target
  ~ components/todos/
      ~ todo-card.tsx                   # Add article element, ARIA enhancements
      ~ todo-list.tsx                   # Add aria-live region for loading
      ~ todo-filters.tsx                # Ensure labels, keyboard flow
      ~ stats-cards.tsx                 # Add aria-live for dynamic values
      ~ pagination.tsx                  # Already has nav + aria-current
  ~ app/
      ~ (dashboard)/layout.tsx          # Add skip-to-content link
```

Legend: `~` modified

## Acceptance Criteria

- [ ] Semantic HTML: `<header>`, `<main>`, `<nav>`, `<article>`, `<form>` used correctly
- [ ] All interactive elements have visible focus indicators
- [ ] `aria-label` on all icon-only buttons and controls without visible labels
- [ ] `aria-live="polite"` on regions that update dynamically (stats, todo list)
- [ ] `aria-current="page"` on active pagination button
- [ ] `aria-invalid` + `aria-describedby` on form fields with errors (React Hook Form + shadcn handles this)
- [ ] Keyboard navigation: Tab through all interactive elements in logical order
- [ ] Escape closes open modals/dialogs (Radix handles this)
- [ ] Focus returns to trigger element after modal closes (Radix handles this)
- [ ] Skip-to-content link for keyboard users

---

## Implementation

### Step 1: Add skip-to-content link in `src/app/(dashboard)/layout.tsx`

Add a visually-hidden skip link as the first focusable element. Give `<main>` an `id`.

```tsx
// Add as first child inside the outer div, before <Header />:
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-background focus:px-4 focus:py-2 focus:text-sm focus:shadow-lg"
>
  Skip to main content
</a>

// Change <main> to:
<main id="main-content" className="container mx-auto px-4 py-6">
  {children}
</main>
```

**Why:** Keyboard users can skip the header navigation and jump straight to content. Hidden by default, visible when focused via Tab.

### Step 2: Update `src/components/layout/header.tsx`

Wrap header actions in `<nav>` for semantic meaning.

```tsx
<header className="border-b bg-background">
  <div className="container mx-auto flex h-16 items-center justify-between px-4">
    <h1 className="text-xl font-bold">Todo App</h1>
    <nav aria-label="User navigation" className="flex items-center gap-4">
      <span className="text-sm text-muted-foreground" aria-label={`Logged in as ${user?.username}`}>
        {user?.username}
      </span>
      <Button variant="outline" size="sm" onClick={logout} aria-label="Logout">
        Logout
      </Button>
    </nav>
  </div>
</header>
```

### Step 3: Update `src/components/todos/todo-card.tsx`

Wrap each card in `<article>` for semantic meaning.

shadcn Card does NOT support `asChild`. Wrap Card content in `<article>` inside:

```tsx
<Card className={isPending ? "opacity-60 transition-opacity" : ""}>
  <article aria-label={`Todo: ${todo.title}`}>
    <CardHeader className="pb-3">
      {/* ... */}
    </CardHeader>
    <CardContent>
      {/* ... */}
    </CardContent>
  </article>
</Card>
```

Also add `aria-label` to Edit and Delete buttons (toggle already has one):

```tsx
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
```

### Step 4: Update `src/components/todos/todo-list.tsx`

Add `aria-live` region so screen readers announce when the list updates.

```tsx
// Wrap the return value in:
<section aria-label="Todo list" aria-live="polite">
  {/* existing loading / empty / grid content */}
</section>
```

**Why:** When filters change or todos are added/removed, screen readers announce the update.

### Step 5: Update `src/components/todos/stats-cards.tsx`

Add `aria-live` so screen readers announce stat changes.

```tsx
// Wrap the cards grid in:
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
```

### Step 6: Verify with keyboard-only navigation

Test this flow using only the keyboard (no mouse):

1. **Tab** through the page: Skip link → Header (username, logout) → Stats → Search → Filter → New Todo → Todo cards (actions) → Pagination
2. **Enter** on "New Todo" → modal opens
3. **Tab** through modal fields → Submit or **Escape** to close
4. **Focus** returns to "New Todo" button after modal closes
5. **Tab** to a todo's Complete button → **Enter** toggles it
6. **Tab** to Delete → **Enter** → confirmation dialog → **Tab** to Cancel/Delete → **Escape** to close

### Step 7: Verify with screen reader

If possible, test with VoiceOver (macOS):
- `Cmd + F5` to enable VoiceOver
- Navigate through the page — all elements should be announced meaningfully
- Stats should read as "Total: 5", not just "5"
- Todo cards should announce their title
- Buttons should announce their purpose ("Complete todo: Buy milk", not just "Complete")

### What's already accessible (from shadcn/Radix)

No changes needed for:
- **Modal focus trap** — Radix Dialog traps Tab inside when open
- **Escape to close** — Radix Dialog/AlertDialog handles this
- **Focus restoration** — Focus returns to trigger after modal closes
- **Form errors** — shadcn Form + React Hook Form automatically adds `aria-invalid` and `aria-describedby`
- **Select dropdown** — Radix Select is fully keyboard accessible
- **Focus indicators** — Tailwind's `focus-visible:ring` already visible on all shadcn components
