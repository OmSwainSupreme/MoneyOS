# Multi-stage Dockerfile for MoneyOS (frontend + backend)
# Build args control which service is built.
# Usage:
#   docker build --target frontend -t moneyos-frontend .
#   docker build --target backend  -t moneyos-backend .

# =====================================================================
# BASE STAGE — shared dependencies
# =====================================================================
FROM node:20-alpine AS base
WORKDIR /app
# Install pnpm for fast installs
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy package manifests
COPY package.json package-lock.json* pnpm-lock.yaml* ./

# =====================================================================
# FRONTEND BUILD
# =====================================================================
FROM base AS frontend-builder
WORKDIR /app

# Install all deps (including dev for build)
RUN pnpm install --frozen-lockfile

# Copy frontend source
COPY apps/frontend ./apps/frontend

# Build frontend
WORKDIR /app/apps/frontend
RUN pnpm run build

# =====================================================================
# FRONTEND RUNTIME
# =====================================================================
FROM node:20-alpine AS frontend
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

# Copy built output
COPY --from=frontend-builder /app/apps/frontend/.next/standalone ./
COPY --from=frontend-builder /app/apps/frontend/.next/static ./.next/static
COPY --from=frontend-builder /app/apps/frontend/public ./public

EXPOSE 3000
CMD ["node", "server.js"]

# =====================================================================
# BACKEND BUILD
# =====================================================================
FROM python:3.11-slim AS backend-builder
WORKDIR /app

# Install uv for fast Python package installs
RUN pip install --no-cache-dir uv

# Copy backend manifests
COPY apps/backend/requirements.txt ./requirements.txt

# Install Python deps into a virtualenv
RUN uv venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# =====================================================================
# BACKEND RUNTIME
# =====================================================================
FROM python:3.11-slim AS backend
WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Copy venv from builder
COPY --from=backend-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy backend source
COPY apps/backend ./apps/backend

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]