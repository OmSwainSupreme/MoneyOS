# Security & Compliance Boundaries

## Overview
This document outlines the planned security boundary for handling sensitive financial data in MoneyOS MVP.

## PII Scrubbing
- Before sending any financial data to third-party LLM APIs, all Personally Identifiable Information (PII) must be scrubbed.
- Sensitive fields such as account numbers, names, emails, and addresses are replaced with generic placeholders.
- A scrubbing service in `apps/backend/services/ai/` will handle this transformation.

## Local Token Masking
- All authentication tokens are masked in logs and stored encrypted.
- Tokens are never persisted in plain text.
- Use environment variables for token configuration.

## Data Encryption
- Data at rest: PostgreSQL encryption at rest
- Data in transit: TLS 1.3 for all API communication
- Use vault services for secret management in production

## Compliance Notes
- MVP will not store raw financial credentials.
- All external API calls are routed through a scrubbing middleware.
- Regular security audits will be performed.