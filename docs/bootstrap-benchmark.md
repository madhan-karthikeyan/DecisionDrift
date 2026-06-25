# Bootstrap V3 Benchmark Report

**Date:** 2026-06-23
**Repos:** 22 evaluated, 0 skipped, 0 crashed

---

## Aggregate Metrics

  Technology candidates: 154 (strong=39, moderate=57, weak=58)
  Suppressed findings/candidates: 100
  Enforceable ADRs generated: 10 (0 duplicates)
  Average latency: 2.6s
  Crash rate: 0/22

---

## Per-Repository Details

### tiangolo/full-stack-fastapi-template

**Status:** ✓
**Repository role:** api_service (async_python_api)
**Technologies:** 15 (0.1s)
**Detected:** SQLAlchemy, Python, JavaScript, JWT, FastAPI, Docker, Alembic, Tailwind CSS, Sentry, React, PostgreSQL, Next.js, pytest, Strapi, GitHub Actions
**Suppressed technologies:** Docker: Docker is tooling and needs explicit deployment policy evidence.; Next.js: No runtime framework import, entrypoint, or route evidence found.; pytest: pytest evidence is test, not a runtime governance decision.; Strapi: No runtime framework import, entrypoint, or route evidence found.; Only generic favicon evidence found.; GitHub Actions: GitHub Actions is tooling and needs explicit deployment policy evidence.
**Suppressed candidates:** Use Alembic for Database Migrations: Alembic evidence is supporting infrastructure, not enough for an ADR without stronger policy evidence.; Use PostgreSQL for Persistent Storage: PostgreSQL evidence is supporting infrastructure, not enough for an ADR without stronger policy evidence.
**Enforceable ADRs:** 4 (0 duplicates)
**ADR titles:** Use SQLAlchemy for relational persistence, Use JWT for API Authentication, Use FastAPI for HTTP APIs, Use React for Frontend UI

**Manual ADR review:**
- Use SQLAlchemy for relational persistence | approve: TODO | reason: TODO
- Use JWT for API Authentication | approve: TODO | reason: TODO
- Use FastAPI for HTTP APIs | approve: TODO | reason: TODO
- Use React for Frontend UI | approve: TODO | reason: TODO

**Manual suppression review:**
- Docker: Docker is tooling and needs explicit deployment policy evidence. | correct: TODO | reason: TODO
- Next.js: No runtime framework import, entrypoint, or route evidence found. | correct: TODO | reason: TODO
- pytest: pytest evidence is test, not a runtime governance decision. | correct: TODO | reason: TODO
- Strapi: No runtime framework import, entrypoint, or route evidence found.; Only generic favicon evidence found. | correct: TODO | reason: TODO
- GitHub Actions: GitHub Actions is tooling and needs explicit deployment policy evidence. | correct: TODO | reason: TODO
- Use Alembic for Database Migrations: Alembic evidence is supporting infrastructure, not enough for an ADR without stronger policy evidence. | correct: TODO | reason: TODO
- Use PostgreSQL for Persistent Storage: PostgreSQL evidence is supporting infrastructure, not enough for an ADR without stronger policy evidence. | correct: TODO | reason: TODO
**Evidence:** {'strong': 7, 'moderate': 5, 'weak': 3}

---

### django/django

**Status:** ✓
**Repository role:** framework (unknown)
**Technologies:** 7 (6.5s)
**Detected:** PostgreSQL, Django, Redis, Python, JavaScript, Alembic, GitHub Actions
**Suppressed technologies:** Django: Django is the repository product, not a governance decision.; GitHub Actions: No runtime evidence found.
**Suppressed candidates:** Use PostgreSQL for Persistent Storage: Framework/product repositories do not produce consumer governance ADRs for implementation technologies.; Use Redis for Caching: Framework/product repositories do not produce consumer governance ADRs for implementation technologies.; Use Alembic for Database Migrations: Framework/product repositories do not produce consumer governance ADRs for implementation technologies.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- Django: Django is the repository product, not a governance decision. | correct: TODO | reason: TODO
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
- Use PostgreSQL for Persistent Storage: Framework/product repositories do not produce consumer governance ADRs for implementation technologies. | correct: TODO | reason: TODO
- Use Redis for Caching: Framework/product repositories do not produce consumer governance ADRs for implementation technologies. | correct: TODO | reason: TODO
- Use Alembic for Database Migrations: Framework/product repositories do not produce consumer governance ADRs for implementation technologies. | correct: TODO | reason: TODO
**Evidence:** {'strong': 2, 'moderate': 4, 'weak': 1}

---

### saleor/saleor

**Status:** ✓
**Repository role:** api_service (unknown)
**Technologies:** 14 (9.6s)
**Detected:** pytest, Uvicorn, Redis, OAuth, JWT, Django, Celery, Sentry, Python, PostgreSQL, JavaScript, Docker, Alembic, GitHub Actions
**Suppressed technologies:** pytest: pytest evidence is test, not a runtime governance decision.; Docker: Docker is tooling and needs explicit deployment policy evidence.; GitHub Actions: GitHub Actions is tooling and needs explicit deployment policy evidence.
**Suppressed candidates:** Use Redis for Caching: Redis evidence is supporting infrastructure, not enough for an ADR without stronger policy evidence.; Use PostgreSQL for Persistent Storage: PostgreSQL evidence is supporting infrastructure, not enough for an ADR without stronger policy evidence.; Use Alembic for Database Migrations: Alembic evidence is supporting infrastructure, not enough for an ADR without stronger policy evidence.
**Enforceable ADRs:** 3 (0 duplicates)
**ADR titles:** Use JWT for API Authentication, Use Django as Web Framework, Use Celery for asynchronous jobs

**Manual ADR review:**
- Use JWT for API Authentication | approve: TODO | reason: TODO
- Use Django as Web Framework | approve: TODO | reason: TODO
- Use Celery for asynchronous jobs | approve: TODO | reason: TODO

**Manual suppression review:**
- pytest: pytest evidence is test, not a runtime governance decision. | correct: TODO | reason: TODO
- Docker: Docker is tooling and needs explicit deployment policy evidence. | correct: TODO | reason: TODO
- GitHub Actions: GitHub Actions is tooling and needs explicit deployment policy evidence. | correct: TODO | reason: TODO
- Use Redis for Caching: Redis evidence is supporting infrastructure, not enough for an ADR without stronger policy evidence. | correct: TODO | reason: TODO
- Use PostgreSQL for Persistent Storage: PostgreSQL evidence is supporting infrastructure, not enough for an ADR without stronger policy evidence. | correct: TODO | reason: TODO
- Use Alembic for Database Migrations: Alembic evidence is supporting infrastructure, not enough for an ADR without stronger policy evidence. | correct: TODO | reason: TODO
**Evidence:** {'strong': 7, 'moderate': 6, 'weak': 1}

---

### psf/requests

**Status:** ✓
**Repository role:** library (unknown)
**Technologies:** 3 (0.1s)
**Detected:** Python, pytest, GitHub Actions
**Suppressed technologies:** pytest: No runtime evidence found.; GitHub Actions: No runtime evidence found.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- pytest: No runtime evidence found. | correct: TODO | reason: TODO
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
**Evidence:** {'moderate': 1, 'weak': 2}

---

### pallets/click

**Status:** ✓
**Repository role:** library (unknown)
**Technologies:** 3 (0.3s)
**Detected:** Python, pytest, GitHub Actions
**Suppressed technologies:** pytest: No runtime evidence found.; GitHub Actions: No runtime evidence found.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- pytest: No runtime evidence found. | correct: TODO | reason: TODO
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
**Evidence:** {'moderate': 1, 'weak': 2}

---

### pytest-dev/pytest

**Status:** ✓
**Repository role:** library (unknown)
**Technologies:** 5 (1.0s)
**Detected:** pytest, Python, Strapi, GitHub Actions, Django
**Suppressed technologies:** pytest: pytest is a testing technology, not a runtime governance decision.; Strapi: No runtime evidence found.; No runtime framework import, entrypoint, or route evidence found.; Only generic favicon evidence found.; GitHub Actions: No runtime evidence found.; Django: No runtime evidence found.; No runtime framework import, entrypoint, or route evidence found.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- pytest: pytest is a testing technology, not a runtime governance decision. | correct: TODO | reason: TODO
- Strapi: No runtime evidence found.; No runtime framework import, entrypoint, or route evidence found.; Only generic favicon evidence found. | correct: TODO | reason: TODO
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
- Django: No runtime evidence found.; No runtime framework import, entrypoint, or route evidence found. | correct: TODO | reason: TODO
**Evidence:** {'strong': 1, 'moderate': 1, 'weak': 3}

---

### spring-projects/spring-petclinic

**Status:** ✓
**Repository role:** unknown (unknown)
**Technologies:** 3 (0.0s)
**Detected:** Docker, Strapi, GitHub Actions
**Suppressed technologies:** Strapi: No runtime framework import, entrypoint, or route evidence found.; Only generic favicon evidence found.; GitHub Actions: No runtime evidence found.
**Suppressed candidates:** Use Docker for Containerized Runtime: Docker is tooling; no strong deterministic governance rule exists yet.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- Strapi: No runtime framework import, entrypoint, or route evidence found.; Only generic favicon evidence found. | correct: TODO | reason: TODO
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
- Use Docker for Containerized Runtime: Docker is tooling; no strong deterministic governance rule exists yet. | correct: TODO | reason: TODO
**Evidence:** {'moderate': 1, 'weak': 2}

---

### jhipster/jhipster

**Status:** ✓
**Repository role:** unknown (unknown)
**Technologies:** 1 (0.0s)
**Detected:** GitHub Actions
**Suppressed technologies:** GitHub Actions: No runtime evidence found.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
**Evidence:** {'weak': 1}

---

### vercel/next.js

**Status:** ✓
**Repository role:** framework (unknown)
**Technologies:** 16 (4.5s)
**Detected:** Rust, JavaScript, Tokio, Tailwind CSS, React, Next.js, Vue, Redis, PostgreSQL, Passport, Jest, JWT, GitHub Actions, Express, Docker, Alembic
**Suppressed technologies:** Next.js: Next.js is the repository product, not a governance decision.; Vue: No runtime evidence found.; Redis: No runtime evidence found.; PostgreSQL: No runtime evidence found.; Passport: No runtime evidence found.; Jest: No runtime evidence found.; JWT: No runtime evidence found.; GitHub Actions: No runtime evidence found.
**Suppressed candidates:** Use React for Frontend UI: Framework/product repositories do not produce consumer governance ADRs for implementation technologies.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- Next.js: Next.js is the repository product, not a governance decision. | correct: TODO | reason: TODO
- Vue: No runtime evidence found. | correct: TODO | reason: TODO
- Redis: No runtime evidence found. | correct: TODO | reason: TODO
- PostgreSQL: No runtime evidence found. | correct: TODO | reason: TODO
- Passport: No runtime evidence found. | correct: TODO | reason: TODO
- Use React for Frontend UI: Framework/product repositories do not produce consumer governance ADRs for implementation technologies. | correct: TODO | reason: TODO
**Evidence:** {'strong': 2, 'moderate': 4, 'weak': 10}

---

### nestjs/nest

**Status:** ✓
**Repository role:** framework (unknown)
**Technologies:** 9 (0.3s)
**Detected:** JavaScript, Express, Docker, Redis, Passport, NestJS, Jest, JWT, GitHub Actions
**Suppressed technologies:** Express: Framework evidence is not sufficient to infer an application decision.; Redis: No runtime evidence found.; Passport: No runtime evidence found.; NestJS: NestJS is the repository product, not a governance decision.; Jest: No runtime evidence found.; JWT: No runtime evidence found.; GitHub Actions: No runtime evidence found.
**Suppressed candidates:** Use Docker for Containerized Runtime: Framework/product repositories do not produce consumer governance ADRs for implementation technologies.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- Express: Framework evidence is not sufficient to infer an application decision. | correct: TODO | reason: TODO
- Redis: No runtime evidence found. | correct: TODO | reason: TODO
- Passport: No runtime evidence found. | correct: TODO | reason: TODO
- NestJS: NestJS is the repository product, not a governance decision. | correct: TODO | reason: TODO
- Jest: No runtime evidence found. | correct: TODO | reason: TODO
- Use Docker for Containerized Runtime: Framework/product repositories do not produce consumer governance ADRs for implementation technologies. | correct: TODO | reason: TODO
**Evidence:** {'strong': 1, 'moderate': 2, 'weak': 6}

---

### strapi/strapi

**Status:** ✓
**Repository role:** framework (unknown)
**Technologies:** 9 (0.7s)
**Detected:** JavaScript, Strapi, React, Passport, Jest, JWT, Alembic, PostgreSQL, GitHub Actions
**Suppressed technologies:** Strapi: Strapi is the repository product, not a governance decision.; Jest: Jest is a testing technology, not a runtime governance decision.; PostgreSQL: No runtime evidence found.; GitHub Actions: No runtime evidence found.
**Suppressed candidates:** Use React for Frontend UI: Framework/product repositories do not produce consumer governance ADRs for implementation technologies.; Use JWT for API Authentication: Framework/product repositories do not produce consumer governance ADRs for implementation technologies.; Use Alembic for Database Migrations: Framework/product repositories do not produce consumer governance ADRs for implementation technologies.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- Strapi: Strapi is the repository product, not a governance decision. | correct: TODO | reason: TODO
- Jest: Jest is a testing technology, not a runtime governance decision. | correct: TODO | reason: TODO
- PostgreSQL: No runtime evidence found. | correct: TODO | reason: TODO
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
- Use React for Frontend UI: Framework/product repositories do not produce consumer governance ADRs for implementation technologies. | correct: TODO | reason: TODO
- Use JWT for API Authentication: Framework/product repositories do not produce consumer governance ADRs for implementation technologies. | correct: TODO | reason: TODO
- Use Alembic for Database Migrations: Framework/product repositories do not produce consumer governance ADRs for implementation technologies. | correct: TODO | reason: TODO
**Evidence:** {'strong': 1, 'moderate': 6, 'weak': 2}

---

### gin-gonic/gin

**Status:** ✓
**Repository role:** framework (unknown)
**Technologies:** 3 (0.0s)
**Detected:** Go, Gin, GitHub Actions
**Suppressed technologies:** Gin: Gin is the repository product, not a governance decision.; GitHub Actions: No runtime evidence found.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- Gin: Gin is the repository product, not a governance decision. | correct: TODO | reason: TODO
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
**Evidence:** {'moderate': 2, 'weak': 1}

---

### go-gitea/gitea

**Status:** ✓
**Repository role:** frontend_app (unknown)
**Technologies:** 10 (0.5s)
**Detected:** Vue, Tailwind CSS, Python, PostgreSQL, JavaScript, Go, Docker, Alembic, Strapi, GitHub Actions
**Suppressed technologies:** Strapi: No runtime framework import, entrypoint, or route evidence found.; Only generic favicon evidence found.; GitHub Actions: No runtime evidence found.
**Suppressed candidates:** Use PostgreSQL for Persistent Storage: Data-access evidence appears in a library/integration context, not an application persistence boundary.; Use Docker for Containerized Runtime: Docker is tooling; no strong deterministic governance rule exists yet.; Use Alembic for Database Migrations: Data-access evidence appears in a library/integration context, not an application persistence boundary.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- Strapi: No runtime framework import, entrypoint, or route evidence found.; Only generic favicon evidence found. | correct: TODO | reason: TODO
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
- Use PostgreSQL for Persistent Storage: Data-access evidence appears in a library/integration context, not an application persistence boundary. | correct: TODO | reason: TODO
- Use Docker for Containerized Runtime: Docker is tooling; no strong deterministic governance rule exists yet. | correct: TODO | reason: TODO
- Use Alembic for Database Migrations: Data-access evidence appears in a library/integration context, not an application persistence boundary. | correct: TODO | reason: TODO
**Evidence:** {'moderate': 8, 'weak': 2}

---

### tokio-rs/tokio

**Status:** ✓
**Repository role:** framework (unknown)
**Technologies:** 3 (0.1s)
**Detected:** Rust, Tokio, GitHub Actions
**Suppressed technologies:** Tokio: Tokio is the repository product, not a governance decision.; GitHub Actions: No runtime evidence found.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- Tokio: Tokio is the repository product, not a governance decision. | correct: TODO | reason: TODO
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
**Evidence:** {'strong': 1, 'moderate': 1, 'weak': 1}

---

### actix/actix-web

**Status:** ✓
**Repository role:** framework (unknown)
**Technologies:** 4 (0.1s)
**Detected:** Rust, Tokio, Actix, GitHub Actions
**Suppressed technologies:** Actix: Actix is the repository product, not a governance decision.; GitHub Actions: No runtime evidence found.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- Actix: Actix is the repository product, not a governance decision. | correct: TODO | reason: TODO
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
**Evidence:** {'strong': 1, 'moderate': 2, 'weak': 1}

---

### GoogleCloudPlatform/microservices-demo

**Status:** ✓
**Repository role:** api_service (unknown)
**Technologies:** 9 (0.1s)
**Detected:** JavaScript, Go, Flask, Docker, SQLAlchemy, Python, PostgreSQL, pytest, GitHub Actions
**Suppressed technologies:** Docker: Docker is tooling and needs explicit deployment policy evidence.; pytest: pytest evidence is test, not a runtime governance decision.; GitHub Actions: GitHub Actions is tooling and needs explicit deployment policy evidence.
**Suppressed candidates:** Use PostgreSQL for Persistent Storage: PostgreSQL evidence is supporting infrastructure, not enough for an ADR without stronger policy evidence.
**Enforceable ADRs:** 2 (0 duplicates)
**ADR titles:** Use Flask as Web Framework, Use SQLAlchemy for relational persistence

**Manual ADR review:**
- Use Flask as Web Framework | approve: TODO | reason: TODO
- Use SQLAlchemy for relational persistence | approve: TODO | reason: TODO

**Manual suppression review:**
- Docker: Docker is tooling and needs explicit deployment policy evidence. | correct: TODO | reason: TODO
- pytest: pytest evidence is test, not a runtime governance decision. | correct: TODO | reason: TODO
- GitHub Actions: GitHub Actions is tooling and needs explicit deployment policy evidence. | correct: TODO | reason: TODO
- Use PostgreSQL for Persistent Storage: PostgreSQL evidence is supporting infrastructure, not enough for an ADR without stronger policy evidence. | correct: TODO | reason: TODO
**Evidence:** {'strong': 4, 'moderate': 3, 'weak': 2}

---

### kubernetes/kubernetes

**Status:** ✓
**Repository role:** library (unknown)
**Technologies:** 3 (2.5s)
**Detected:** Go, Docker, Python
**Suppressed candidates:** Use Docker for Containerized Runtime: Docker is tooling; no strong deterministic governance rule exists yet.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- Use Docker for Containerized Runtime: Docker is tooling; no strong deterministic governance rule exists yet. | correct: TODO | reason: TODO
**Evidence:** {'strong': 2, 'moderate': 1}

---

### argoproj/argo-cd

**Status:** ✓
**Repository role:** frontend_app (unknown)
**Technologies:** 8 (0.6s)
**Detected:** Go, React, JavaScript, Docker, Strapi, Python, Jest, GitHub Actions
**Suppressed technologies:** Strapi: No runtime evidence found.; No runtime framework import, entrypoint, or route evidence found.; Only generic favicon evidence found.; Python: No runtime evidence found.; Jest: No runtime evidence found.; GitHub Actions: No runtime evidence found.
**Suppressed candidates:** Use Docker for Containerized Runtime: Docker is tooling; no strong deterministic governance rule exists yet.
**Enforceable ADRs:** 1 (0 duplicates)
**ADR titles:** Use React for Frontend UI

**Manual ADR review:**
- Use React for Frontend UI | approve: TODO | reason: TODO

**Manual suppression review:**
- Strapi: No runtime evidence found.; No runtime framework import, entrypoint, or route evidence found.; Only generic favicon evidence found. | correct: TODO | reason: TODO
- Python: No runtime evidence found. | correct: TODO | reason: TODO
- Jest: No runtime evidence found. | correct: TODO | reason: TODO
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
- Use Docker for Containerized Runtime: Docker is tooling; no strong deterministic governance rule exists yet. | correct: TODO | reason: TODO
**Evidence:** {'strong': 1, 'moderate': 3, 'weak': 4}

---

### hashicorp/vault

**Status:** ✓
**Repository role:** library (unknown)
**Technologies:** 5 (0.6s)
**Detected:** JavaScript, Go, Docker, Strapi, GitHub Actions
**Suppressed technologies:** Strapi: No runtime framework import, entrypoint, or route evidence found.; Only generic favicon evidence found.; GitHub Actions: No runtime evidence found.
**Suppressed candidates:** Use Docker for Containerized Runtime: Docker is tooling; no strong deterministic governance rule exists yet.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- Strapi: No runtime framework import, entrypoint, or route evidence found.; Only generic favicon evidence found. | correct: TODO | reason: TODO
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
- Use Docker for Containerized Runtime: Docker is tooling; no strong deterministic governance rule exists yet. | correct: TODO | reason: TODO
**Evidence:** {'strong': 2, 'moderate': 1, 'weak': 2}

---

### huggingface/transformers

**Status:** ✓
**Repository role:** library (unknown)
**Technologies:** 7 (23.5s)
**Detected:** Python, PostgreSQL, Docker, pytest, Uvicorn, GitHub Actions, FastAPI
**Suppressed technologies:** pytest: pytest is a testing technology, not a runtime governance decision.; Uvicorn: No runtime evidence found.; GitHub Actions: No runtime evidence found.; FastAPI: No runtime evidence found.; No runtime framework import, entrypoint, or route evidence found.
**Suppressed candidates:** Use PostgreSQL for Persistent Storage: Data-access evidence appears in a library/integration context, not an application persistence boundary.; Use Docker for Containerized Runtime: Docker is tooling; no strong deterministic governance rule exists yet.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- pytest: pytest is a testing technology, not a runtime governance decision. | correct: TODO | reason: TODO
- Uvicorn: No runtime evidence found. | correct: TODO | reason: TODO
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
- FastAPI: No runtime evidence found.; No runtime framework import, entrypoint, or route evidence found. | correct: TODO | reason: TODO
- Use PostgreSQL for Persistent Storage: Data-access evidence appears in a library/integration context, not an application persistence boundary. | correct: TODO | reason: TODO
- Use Docker for Containerized Runtime: Docker is tooling; no strong deterministic governance rule exists yet. | correct: TODO | reason: TODO
**Evidence:** {'strong': 3, 'moderate': 1, 'weak': 3}

---

### langchain-ai/langchain

**Status:** ✓
**Repository role:** library (unknown)
**Technologies:** 8 (5.1s)
**Detected:** pytest, SQLAlchemy, Python, Redis, Uvicorn, GitHub Actions, FastAPI, Docker
**Suppressed technologies:** pytest: pytest is a testing technology, not a runtime governance decision.; Uvicorn: No runtime evidence found.; GitHub Actions: No runtime evidence found.; FastAPI: No runtime evidence found.; No runtime framework import, entrypoint, or route evidence found.; Docker: No runtime evidence found.
**Suppressed candidates:** Use SQLAlchemy for relational persistence: Data-access evidence appears in a library/integration context, not an application persistence boundary.; Use Redis for Caching: Redis evidence is supporting infrastructure, not enough for an ADR without stronger policy evidence.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- pytest: pytest is a testing technology, not a runtime governance decision. | correct: TODO | reason: TODO
- Uvicorn: No runtime evidence found. | correct: TODO | reason: TODO
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
- FastAPI: No runtime evidence found.; No runtime framework import, entrypoint, or route evidence found. | correct: TODO | reason: TODO
- Docker: No runtime evidence found. | correct: TODO | reason: TODO
- Use SQLAlchemy for relational persistence: Data-access evidence appears in a library/integration context, not an application persistence boundary. | correct: TODO | reason: TODO
- Use Redis for Caching: Redis evidence is supporting infrastructure, not enough for an ADR without stronger policy evidence. | correct: TODO | reason: TODO
**Evidence:** {'strong': 3, 'moderate': 1, 'weak': 4}

---

### microsoft/vscode

**Status:** ✓
**Repository role:** library (unknown)
**Technologies:** 9 (1.5s)
**Detected:** JavaScript, Tokio, Rust, Express, React, Python, Jest, GitHub Actions, Docker
**Suppressed technologies:** Express: Framework evidence is not sufficient to infer an application decision.; React: No runtime evidence found.; Python: No runtime evidence found.; Jest: No runtime evidence found.; GitHub Actions: No runtime evidence found.; Docker: No runtime evidence found.
**Enforceable ADRs:** 0 (0 duplicates)

**Manual suppression review:**
- Express: Framework evidence is not sufficient to infer an application decision. | correct: TODO | reason: TODO
- React: No runtime evidence found. | correct: TODO | reason: TODO
- Python: No runtime evidence found. | correct: TODO | reason: TODO
- Jest: No runtime evidence found. | correct: TODO | reason: TODO
- GitHub Actions: No runtime evidence found. | correct: TODO | reason: TODO
**Evidence:** {'strong': 1, 'moderate': 3, 'weak': 5}

---
