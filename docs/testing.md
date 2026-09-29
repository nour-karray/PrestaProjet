# Test strategy

TrainFlow AI keeps the legacy FastAPI suite as a compatibility oracle until
the Spring API cutover is complete.

| Scope | Command | Purpose |
| --- | --- | --- |
| Spring backend | `cd backend && mvn verify` | Unit, MVC, security, storage, PDF and MySQL integration tests |
| FastAPI reference | `cd backend-python && python -m pytest -q` | Detect behavioural regressions during migration |
| Frontend | `cd frontend && npm run lint && npm test -- --run && npm run build` | Lint, component/API-contract tests and production build |

The MySQL Testcontainers test is skipped automatically when Docker is not
available. It must run in CI where Docker is provided. Tests never use the
development database and no suite is allowed to create, alter or delete its
tables.

At the Phase 12 checkpoint the local results were:

- Spring: 46 tests passed (the Docker-backed integration test may be skipped);
- FastAPI compatibility suite: 170 passed, 1 skipped;
- frontend: 49 passed, ESLint and Next.js production build successful.
