# CDSS (Contoso Deep Space Station) — Signal Routing Guide

> **Last updated:** July 2025
> **Author:** Raj Mehta, Station Operations Desk Manager
> **Status:** DRAFT — some sections still being finalized after the Q2 crew rotation

---

## How to use this guide

When a signal comes in, identify the **issue type** from the table below and route to the listed **owning team**. If you're unsure, escalate to the Operations Desk Lead.

## Priority Definitions

| Priority | Label | Response SLA | Resolution SLA | When to use |
|---|---|---|---|---|
| P1 | Critical | 15 min | 4 hours | Hull breach, hostile contact, life support failure, commander-impacting |
| P2 | High | 1 hour | 8 hours | Major system malfunction, no workaround, multiple crew affected |
| P3 | Medium | 4 hours | 3 business days | Issue with workaround available, single crew member blocked but non-urgent |
| P4 | Low | 1 business day | 10 business days | Minor inconvenience, cosmetic issue, feature request, general question |

**Override rule:** Any signal mentioning potential data breach / telemetry leak, regulatory issue, or compliance audit is automatically **P1** regardless of other factors.

---

## Routing Table

### Crew Identity & Airlock Control

| Issue type | Route to | Notes |
|---|---|---|
| Airlock code reset | Crew Identity & Airlock Control | Self-service portal handles most; only escalate if SSPR fails |
| Biometric lock failure | Crew Identity & Airlock Control | Check for brute-force indicators first — if suspicious, also alert Threat Response Command |
| New crew member registration | Crew Identity & Airlock Control | Requires commanding officer approval in ServiceNow |
| Single sign-on to station systems | Crew Identity & Airlock Control | Verify the app is in the Entra ID gallery first |
| Directory sync issues | Crew Identity & Airlock Control | Usually Entra Connect related |
| Service account requests | Crew Identity & Airlock Control | Requires security review before provisioning |

### Spacecraft Systems Engineering

| Issue type | Route to | Notes |
|---|---|---|
| Terminal/module hardware failure | Spacecraft Systems Engineering | If under warranty, initiate vendor RMA |
| ShipOS crash / blue screen | Spacecraft Systems Engineering | Collect crash dump before reimaging |
| Software deployment on station terminals | Spacecraft Systems Engineering | Must be on the approved software list |
| Intune enrollment | Spacecraft Systems Engineering | New crew should be auto-enrolled |
| 3D fabricator issues | Spacecraft Systems Engineering | Check if it's a networked fabricator (→ Deep Space Communications) or direct-connected |
| Mobile device issues | Spacecraft Systems Engineering | Station-managed devices only |
| Slow terminal | Spacecraft Systems Engineering | Run hardware diagnostics first |

### Deep Space Communications

| Issue type | Route to | Notes |
|---|---|---|
| Subspace relay connectivity | Deep Space Communications | Check if crew member's credentials are expired first (→ Crew Identity & Airlock Control if so) |
| RF mesh / comm relay issues | Deep Space Communications | — |
| Name Resolution Service failures | Deep Space Communications | — |
| Signal barrier rule requests | Deep Space Communications | Requires security approval from Threat Response Command |
| Bandwidth / latency | Deep Space Communications | Get specific times and affected services |
| Video conferencing quality | Deep Space Communications | If it's a HERMES-specific issue, try Mission Software Operations first |

### Mission Software Operations

| Issue type | Route to | Notes |
|---|---|---|
| Navigation systems (SAP) errors or access | Mission Software Operations | — |
| Salesforce issues | Mission Software Operations | — |
| Sensor array terminal (Bloomberg) | Mission Software Operations | Physical hardware issues go to Spacecraft Systems Engineering |
| Station Suite 365 issues | Mission Software Operations | Licensing issues specifically — general Station Suite 365 outages are Deep Space Communications |
| Internal station app bugs | Mission Software Operations | — |
| Application licensing | Mission Software Operations | — |

### Threat Response Command

| Issue type | Route to | Notes |
|---|---|---|
| Signal injection attack received | Threat Response Command | Forward original as attachment to phishing@contoso.com |
| Malicious code / hostile programs | Threat Response Command | Isolate device from station network immediately |
| Data breach / telemetry leak / unauthorized access | Threat Response Command | Mandatory P1 escalation |
| Security certificate issues | Threat Response Command | — |
| Compliance / audit requests | Threat Response Command | — |

### Telemetry & Data Core

| Issue type | Route to | Notes |
|---|---|---|
| DataVault (SharePoint) site access | Telemetry & Data Core | — |
| CrewDrive sync issues | Telemetry & Data Core | Large file sync problems are common; check file count limits |
| Database access request | Telemetry & Data Core | Requires data owner approval |
| Backup / restore request | Telemetry & Data Core | — |
| File share access | Telemetry & Data Core | Legacy file shares only; new requests should use DataVault (SharePoint) |

---

## Known gaps in this guide

> **Raj's note:** The following areas still need to be sorted out. For now, use your best judgment or escalate to the Operations Desk Lead.

- **Multi-factor biometric authentication issues** — Could be Crew Identity & Airlock Control (crew setup), Threat Response Command (policy enforcement), or Spacecraft Systems Engineering (authenticator app issues). We haven't agreed on a single owner.
- **HERMES / collaboration issues** — Is it a Deep Space Communications issue (call quality), Mission Software Operations issue (HERMES app crash), or Spacecraft Systems Engineering issue (headset/camera)? Depends on the symptoms.
- **Station infrastructure requests** — Azure subscription access, VM requests, etc. Telemetry & Data Core handles some, but we don't have a formal station infrastructure ops team yet.
- **Crew arrival / departure** — Touches Crew Identity & Airlock Control (accounts), Spacecraft Systems Engineering (hardware), Mission Software Operations (licenses), and Telemetry & Data Core (access). There's a workflow for this but it's manual and breaks constantly.
- **3D fabricator and scanning** — Networked fabricators are Deep Space Communications, direct-connected fabricators are Spacecraft Systems Engineering, scan-to-comms failures could be either.

---

## Escalation rules

1. **P1 signals** — Must be acknowledged within 15 minutes. If the assigned team doesn't acknowledge, auto-escalate to Operations Desk Lead.
2. **Security incidents** — Always route to Threat Response Command. If it also affects another team's domain (e.g., compromised crew credentials = Crew Identity & Airlock Control + Threat Response Command), route to Threat Response Command as primary and Crew Identity & Airlock Control as secondary.
3. **Command staff tickets** — Admiral and Commander-level signals are auto-flagged. Treat as one priority level higher than normal assessment.
4. **Repeat signals** — If the same reporter has filed 3+ signals in 7 days for the same issue, escalate to the team lead for root cause investigation.
