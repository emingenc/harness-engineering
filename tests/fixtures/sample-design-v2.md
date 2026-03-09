# Design: Authentication Module v2

## Problem Statement

The application lacks a unified authentication module with metrics tracking.

<!-- ANNOTATION: Use JWT with short-lived tokens and refresh rotation -->

## Proposed Solution

Implement a centralized auth module using JWT tokens with timing and metrics.

<!-- ANNOTATION: Add rate limiting to login endpoints -->
<!-- ANNOTATION: Track attempt counts for security monitoring -->

## Architecture

The auth module sits between the API gateway and service layer:

```
Client -> API Gateway -> Auth Module -> Service Layer
```

Key components:
- Token issuer/validator
- Session store (Redis-backed)
- RBAC policy engine
- Metrics collector

## Trade-offs

| Approach | Pro | Con |
|---|---|---|
| JWT | Stateless, scalable | Token revocation complexity |
| Session cookies | Simple revocation | Server state required |

Decision: JWT with Redis-backed revocation list.

## Verification Strategy

| Check | Type | Command |
|-------|------|---------|
| Token generation | Unit | pytest tests/test_auth.py -k token |
| Login flow | Integration | pytest tests/test_auth.py -k login |
| Security audit | Manual | OWASP auth checklist |

## Micro-Task Breakdown

1. Create auth module with JWT token issuer -- scope: S
2. Add refresh token rotation and session store -- scope: M
3. Implement RBAC policy engine with role definitions -- scope: M

### File Changes

| File | Change | Description |
|---|---|---|
| `src/auth/token.py` | Create | JWT issuer and validator |
| `src/auth/session.py` | Create | Redis-backed session store with rotation |
| `src/auth/rbac.py` | Create | Role-based access control engine |
| `tests/test_auth.py` | Create | Auth module test suite |
