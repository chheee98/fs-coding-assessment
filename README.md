# Full Stack Engineering Assessment – Production TODO Application

Welcome to the Full Stack Engineering Assessment! This challenge evaluates your ability to build a **production-ready TODO application** with modern architecture patterns, authentication, database integration, and comprehensive testing.

This assessment was completed by pair programming with [Claude Code](https://claude.com/claude-code). See [`CLAUDE.md`](./CLAUDE.md) for more details on the approach and workflow.

---

## 🎯 Objective

Build a complete TODO application with:

- **Backend**: RESTful API using FastAPI with PostgreSQL/SQLite database, JWT authentication, and comprehensive testing
- **Frontend**: Next.js application with state management, authentication flow, optimistic updates, and error handling

---

## 📋 Detailed Requirements

Please check:

- [`/backend/README.md`](./backend/README.md) for detailed Backend requirements
- [`/frontend/README.md`](./frontend/README.md) for detailed Frontend requirements

---

## 📁 Documentation

### Decisions & Trade-offs

Architecture decisions made during development, with reasoning and trade-offs for each.

- [`docs/backend-decisions_and_tradeoffs.md`](./docs/backend-decisions_and_tradeoffs.md) — 19 backend decisions (architecture, CRUD, stats, testing, reusable patterns)
- [`docs/frontend-decisions_and_tradeoffs.md`](./docs/frontend-decisions_and_tradeoffs.md) — 9 frontend decisions (auth, todo management, optimistic updates, accessibility)
- [`docs/beyond-spec-status-transitions-and-duedate.md`](./docs/beyond-spec-status-transitions-and-duedate.md) — Beyond-spec feature: proper status transitions and due date editing (separate PR)
- [`docs/backend-ai-review.md`](./docs/backend-ai-review.md) — AI-assisted code review of the backend

---

## 🚀 Submission Requirements

### Must Include:

1. **GitHub Repository** with:
   - Clear README with setup instructions
   - `.env.example` files for both frontend and backend
2. **Documentation**:
   - API documentation
   - Architecture decisions and trade-offs
3. **Tests**:
   - Test suites
   - Instructions to run tests

4. **Working Application**:
   - Both services run independently
   - Successful frontend-backend integration
   - All features functional

### Evaluation Criteria:

- **Code Quality** (30%): Clean, maintainable, well-structured code
- **Functionality** (25%): All required features working correctly
- **Architecture** (20%): Proper separation of concerns, scalable design
- **Testing** (15%): Comprehensive test coverage
- **Security** (10%): Authentication, validation, secure practices

---

Good luck! We're excited to see your solution. 🚀

**Questions?** Contact us via invitation email and we'll respond.
