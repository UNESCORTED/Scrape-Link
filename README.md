# SIH 2026 E-Waste Formal Recycling Platform

This repository is for the SIH 2026 Problem Statement 229 project: an offline-tolerant, vernacular e-waste formalization platform for India.

The repository name is `Scrape-Link`, but the project is not a web scraping application.

## Current Phase

Phase 1 is the local development environment:

- PostgreSQL with PostGIS for location-aware recycler matching
- Redis for cache/session support, optional during local development
- MinIO for local S3-compatible object storage
- FastAPI backend service

## Getting Started

1. Copy `.env.example` to `.env`.
2. Keep the placeholder values for local development, or change them if needed.
3. Start the local services with Docker Compose:

```bash
docker compose up --build
```

The backend health endpoint will be available at:

```text
http://localhost:8000/health
```

## Implementation Order

We are following the master prompt incrementally:

1. Docker Compose and environment setup
2. Backend database models, Alembic migration, and seed data
3. Backend auth and CRUD APIs
4. Backend services for matching, pricing, anomaly detection, and valuation
5. Minimal ML pipeline
6. Mobile Flutter app
7. Recycler dashboard
8. End-to-end tests and documentation
