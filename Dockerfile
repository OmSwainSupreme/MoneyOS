# Multi-stage Dockerfile for MoneyOS (frontend + backend)
# Build args control which service is built.
# Usage:
#   docker build --target frontend -t moneyos-frontend .
#   docker build --target backend  -t moneyos-backend .

# =====================================================================
# BASE STAGE - shared dependencies
# =====================================================================
FROM node:20-alpine AS base
WORKDIR /app
# Frontend uses npm (package-lock.json) + Vite. No pnpm/corepack needed.

# =====================================================================
# FRONTEND BUILD
# =====================================================================
FROM base AS frontend-builder
WORKDIR /app

# npm workspaces install: copy the root manifest + lockfile and every
# workspace package.json first so `npm ci` resolves the full tree from the
# committed lockfile (respecting root overrides) with maximum layer caching.
COPY package.json package-lock.json ./
COPY apps/frontend/package.json ./apps/frontend/package.json
COPY packages/shared/package.json ./packages/shared/package.json
RUN npm ci

# Copy sources and build the frontend workspace (Vite -> dist/).
COPY packages/shared ./packages/shared
COPY apps/frontend ./apps/frontend
RUN npm run build --workspace @moneyos/frontend

# =====================================================================
# FRONTEND RUNTIME
# =====================================================================
FROM node:20-alpine AS frontend
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

# Copy built app from the builder. In an npm workspaces install the
# node_modules tree and workspace symlinks live at the repo root, so the
# runtime WORKDIR stays /app and we copy with absolute destinations.
# The root manifest is required so `npm run preview --workspace` resolves.
COPY --from=frontend-builder /app/package.json ./package.json
COPY --from=frontend-builder /app/package-lock.json ./package-lock.json
COPY --from=frontend-builder /app/node_modules ./node_modules
COPY --from=frontend-builder /app/apps/frontend ./apps/frontend
COPY --from=frontend-builder /app/packages/shared ./packages/shared

EXPOSE 3000
# TanStack Start build is served by Vite preview on the configured port.
CMD ["npm", "run", "preview", "--workspace", "@moneyos/frontend", "--", "--host", "0.0.0.0", "--port", "3000"]

# =====================================================================
# BACKEND BUILD
# =====================================================================
FROM python:3.11-slim AS backend-builder
WORKDIR /app

# Install uv for fast Python package installs
RUN pip install --no-cache-dir uv

# Copy backend manifests
COPY apps/backend/requirements.txt ./apps/backend/requirements.txt

# Install Python deps into a virtualenv
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv --no-cache-dir -r apps/backend/requirements.txt

# =====================================================================
# BACKEND RUNTIME
# =====================================================================
FROM python:3.11-slim AS backend
WORKDIR /app/apps/backend
ENV PYTHONPATH=/app/apps/backend
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Copy venv from builder
COPY --from=backend-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy backend source (build context is the repository root) into the
# working directory so `main:app` resolves from WORKDIR=/app/apps/backend.
COPY apps/backend ./

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]