# Security review pack: Acme Fibre support assistant

**Version:** … · **Reviewer:** Acme security team · **Date:** …

## 1. Data flow

Diagram: `diagram.excalidraw.svg` in this folder (email → redaction → agent → MCP tools → Acme systems → reply).

## 2. Threat model (STRIDE)

| Category | Threat | Mitigation | Evidence |
|---|---|---|---|
| Spoofing | | | |
| Tampering | | | |
| Repudiation | | | audit log (project 4, step 4) |
| Information disclosure | | | |
| Denial of service | | | |
| Elevation of privilege | prompt injection asks for a big refund | Cedar policy before payment | red-team result (project 4, step 6) |

## 3. Personal data

What the agent sees: … · Redaction in logs and traces: … · Retention: … · Who can read logs: …

## 4. Identity and access

Link or copy the identity matrix from project 4.

## 5. Residual risks

| Risk | Likelihood | Impact | Owner at Acme | Accept? |
|---|---|---|---|---|
| | | | | |
