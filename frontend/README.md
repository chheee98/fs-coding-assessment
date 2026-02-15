# Frontend Assessment – To-Do Application with Next.js

## 📌 Overview

This assessment evaluates your **frontend engineering skills**. You'll build a production-ready todo application with authentication, advanced state management, optimistic updates, comprehensive error handling, and testing.

**Key Focus Areas**:

- Next.js App Router with server & client components
- Authentication flow and protected routes
- Global state management (Context API)
- Optimistic UI updates and error handling
- Form validation and user feedback
- Performance optimization and accessibility
- Responsive design with Tailwind CSS

---

## ⚙️ Getting Started

### Prerequisites

- Node.js (v22 or later)
- Backend API running on `http://localhost:8000`

### Install dependencies

```bash
npm install
```

### Environment Setup

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Start dev server

```bash
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000)

### Code Formatting

This project uses [Prettier](https://prettier.io/) for consistent code formatting with [prettier-plugin-tailwindcss](https://github.com/tailwindlabs/prettier-plugin-tailwindcss) for automatic Tailwind class sorting.

```bash
npm run format          # Format all files
npm run format:check    # Check formatting without changes (CI)
npm run lint            # Run ESLint (formatting rules disabled — Prettier handles them)
npm run type-check      # Run TypeScript type checking
```

---

## ✅ Required Tasks

### Task 1: Authentication System

**Pages**: `/login`, `/register`

Implement complete authentication:

- [ ] Registration page with form validation
  - Username and password validation (allowed characters and length)
  - Display validation errors
- [ ] Login page
  - Username and password fields
  - Error handling for invalid credentials
- [ ] JWT token management
  - Store tokens securely (httpOnly cookies or localStorage with XSS protection)
  - Handle token expiration gracefully
- [ ] Protected routes
  - Redirect to login if not authenticated
  - Middleware or HOC for route protection
- [ ] User profile display
  - Show logged-in user info in header
  - Logout functionality (clear token in frontend)

### Task 2: Todo Management

Build comprehensive todo interface:

#### List View

- [ ] Display all todos and paginated (20 per page)
- [ ] Filtering by:
  - Priority (HIGH, MEDIUM, LOW)
- [ ] Search by title functionality (debounced, min 2 chars)
- [ ] Empty states with helpful messages
- [ ] Spinner during fetch
- [ ] Infinite scroll or pagination controls

#### Todo Item Features

- [ ] View todo details (only owner)
- [ ] Quick complete/uncomplete toggle (only owner)
- [ ] Editing capability (only owner)
- [ ] Delete with confirmation modal (only owner)
- [ ] Visual indicators for:
  - Priority level (colors/badges)

#### Create/Edit Forms

- [ ] Modal or slide-over for todo creation
- [ ] Form fields:
  - Title (required, max 200 chars)
  - Description (textarea)
  - Priority selector
- [ ] Real-time validation
- [ ] Cancel and save actions
- [ ] Form dirty state handling (warn before leaving)

### Task 3: Optimistic Updates & Error Handling

Implement production-ready UX patterns:

#### Optimistic Updates

- [ ] Immediately update UI when user takes action
- [ ] Show pending state (e.g., opacity, spinner)

#### Error Handling

- [ ] Error boundaries for React errors
- [ ] API error handling with retry logic
- [ ] Toast notifications for success/error
- [ ] Form validation errors displayed inline

### Task 4: Accessibility & UX

- [ ] Semantic HTML throughout
- [ ] ARIA labels and roles
- [ ] Keyboard navigation support (Tab, Enter, Escape)
- [ ] Screen reader friendly

### Task 5: Responsive Design

Using Tailwind CSS:

- [ ] Mobile-first approach
- [ ] Adaptive layouts (grid/flex)
- [ ] Work on multiple device sizes

---

## ✅ Submission Checklist

Before submitting:

- [ ] All features implemented and working
- [ ] No TypeScript errors (`npm run type-check`)
- [ ] No linting errors (`npm run lint`)
- [ ] No formatting issues (`npm run format:check`)
- [ ] Responsive on mobile, tablet, desktop
- [ ] Accessible (keyboard navigation, screen reader)
- [ ] README updated with setup instructions
- [ ] `.env.example` included
- [ ] Code is well-documented and formatted

---

**Good luck!** Build something you'd be proud to show in a production environment. 🚀
