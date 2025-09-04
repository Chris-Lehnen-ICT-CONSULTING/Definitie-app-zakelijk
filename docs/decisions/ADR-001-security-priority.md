# ADR-001: Security Priority for Single-User MVP

## Status
**Accepted**

## Context
The Definitie-app is currently designed and deployed as a single-user application. The primary user is the developer/owner who runs the application locally on their own machine. There is no multi-user access, no shared database, and no external API exposure.

The application currently has:
- No authentication system implemented (Epic 6: 0% complete)
- No role-based access control
- No API key management for external access
- No data encryption at rest
- No audit logging for compliance

## Decision
We have decided to **defer all security implementation to LOW priority (P3)** for the MVP phase. This affects all SEC-* user stories (SEC-001 through SEC-005).

Security features will only become critical when:
- The application transitions to multi-user support
- The application is exposed via public API
- Multiple users need to access shared data
- Compliance requirements demand audit trails

## Consequences

### Positive
- Faster MVP delivery by focusing on core functionality
- Reduced complexity during initial development
- No unnecessary overhead for single-user scenario
- Resources can focus on features that provide immediate value

### Negative
- Technical debt accumulation if multi-user is needed later
- No protection against local machine compromise
- SQLite database remains unencrypted
- No audit trail for actions performed

### Mitigation
- Security architecture is documented and ready for implementation
- Authentication hooks exist in the codebase (auth/ folder)
- Migration path to multi-user is clear
- Security can be implemented modularly when needed

## Implementation Notes
- All SEC-* stories moved from P0/P1 to P3 priority
- MASTER-EPICS-USER-STORIES.md updated to reflect this decision
- CLAUDE.md updated with single-user application context
- Security Epic 6 marked as "Low" priority instead of "CRITICAL"

## Date
2025-01-04

## Review Date
2025-04-01 (Q2 2025) - Reassess if multi-user functionality is needed

## Authors
- Chris Lehnen (Product Owner)
- Documentation Standards Guardian (AI Agent)
