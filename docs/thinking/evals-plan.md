# Evals Dataset Strategy & Plan

## Problem Statement

The current eval dataset contains only 25 sample tickets (with gold answers) and 50 public eval tickets (no gold). We need 1k-10k unique, diverse, balanced tests that cover the full spectrum of IT support triage scenarios for Contoso Financial Services.

## Approach: Template-Based Parametric Generation

We use a **data-driven scenario generator** that combines:
1. **~300+ unique scenario archetypes** — each representing a distinct IT support situation
2. **Parametric variation** — different reporters, departments, writing styles, channels, dates
3. **Deterministic gold answers** — correct triage decisions derived from scenario definitions
4. **Cross-cutting modifiers** — VIP, urgency contradictions, multi-issue, prompt injection, etc.

### Target: ~2,500 tickets (expandable to 10k)

## Category Balance (8 categories)

| Category | Target % | ~Count | Notes |
|---|---|---|---|
| Access & Authentication | 13% | 325 | Password resets, MFA, SSO, badge access, account lockouts |
| Hardware & Peripherals | 13% | 325 | Laptops, monitors, printers, docking stations, phones |
| Network & Connectivity | 13% | 325 | VPN, WiFi, DNS, firewall, bandwidth, latency |
| Software & Applications | 13% | 325 | Crashes, installs, updates, licensing, compatibility |
| Security & Compliance | 13% | 325 | Phishing, data breach, DLP, compliance violations, suspicious activity |
| Data & Storage | 13% | 325 | Backup, database, cloud storage, ETL, data loss |
| General Inquiry | 10% | 250 | How-to, onboarding, offboarding, process questions |
| Not a Support Ticket | 12% | 300 | Auto-replies, spam, thank-you, FYI, test messages, wrong department |

## Priority Distribution (within actionable categories)

| Priority | Target % | Notes |
|---|---|---|
| P1 | 12% | Critical: production down, security breach, VIP blocked |
| P2 | 25% | High: significant impact, deadline-driven |
| P3 | 38% | Medium: standard issues, workarounds available |
| P4 | 25% | Low: cosmetic, informational, nice-to-have |

## Channel Distribution

| Channel | Target % | Style |
|---|---|---|
| email | 30% | Verbose, formal, may include signatures/threads |
| chat | 25% | Terse, informal, abbreviations |
| portal | 25% | Structured, form-like |
| phone | 20% | Transcription artifacts, filler words, garbled |

## Cross-Cutting Diversity Dimensions

### Writing Style Modifiers (~applies to % of tickets)
- **Formal/professional** — 30%
- **Casual/informal** — 25%
- **Panicked/urgent** — 10%
- **Technical/jargon-heavy** — 15%
- **Vague/incomplete** — 10%
- **Verbose/over-detailed** — 10%

### Special Scenario Modifiers
- **VIP reporters** (C-suite, SVP+) — 5% → priority bump + escalation
- **Multi-issue tickets** — 8% → multiple problems in one ticket
- **Contradictory signals** — 5% → says "low priority" but symptoms are critical
- **Repeat/recurring issues** — 5% → references previous tickets
- **Time-critical deadlines** — 8% → audit, client meeting, go-live
- **Emotional/frustrated reporter** — 5% → threatening to escalate, angry tone
- **Phone transcription garbled** — 5% → speech-to-text artifacts
- **Multilingual content** — 3% → non-English phrases mixed in
- **Base64/encoded content** — 3% → embedded images, encoded data in description
- **AI safety: prompt injection** — 3% → attempts to manipulate triage system
- **AI safety: social engineering** — 2% → impersonation, authority manipulation
- **Conversation history** — 5% → forwarded threads, reply chains
- **Attachment references** — 10% → screenshots, logs, error dumps referenced
- **Multiple participants** — 3% → CC'd people, "on behalf of" requests
- **Ambiguous routing** — 8% → falls in gray areas between teams

## Missing Information Vocabulary (16 values)

Balanced coverage across all 16 constrained vocabulary items:
- affected_system, error_message, steps_to_reproduce, affected_users
- environment_details, timestamp, previous_ticket_id, contact_info
- device_info, application_version, network_location, business_impact
- reproduction_frequency, screenshot_or_attachment, authentication_method, configuration_details

## Team Routing Balance

| Team | Target % | Primary Categories |
|---|---|---|
| Identity & Access Management | 17% | Access & Auth |
| Endpoint Engineering | 20% | Hardware, Software |
| Network Operations | 17% | Network |
| Enterprise Applications | 17% | Software |
| Security Operations | 15% | Security & Compliance |
| Data Platform | 14% | Data & Storage |

## Implementation Architecture

```
docs/eval/
├── generate_evals.py              # Entry point — CLI to generate datasets
├── generator/
│   ├── __init__.py
│   ├── models.py                  # Pydantic models for scenarios, tickets, gold
│   ├── scenarios/
│   │   ├── __init__.py
│   │   ├── access_auth.py         # Access & Authentication scenarios
│   │   ├── hardware.py            # Hardware & Peripherals scenarios
│   │   ├── network.py             # Network & Connectivity scenarios
│   │   ├── software.py            # Software & Applications scenarios
│   │   ├── security.py            # Security & Compliance scenarios
│   │   ├── data_storage.py        # Data & Storage scenarios
│   │   ├── general_inquiry.py     # General Inquiry scenarios
│   │   ├── not_a_ticket.py        # Not a Support Ticket scenarios
│   │   └── edge_cases.py          # Cross-cutting edge cases
│   ├── reporters.py               # Reporter pool (names, emails, depts)
│   ├── modifiers.py               # Cross-cutting modifiers (VIP, urgency, etc.)
│   ├── text_variation.py          # Writing style & template expansion
│   ├── balancer.py                # Ensures distribution targets
│   └── validator.py               # Schema validation
```

## Unique Scenario Ideas by Category

### Access & Authentication (~40 unique scenarios)
1. Password expired / forced reset
2. MFA push not arriving on phone
3. MFA locked out — lost/stolen phone
4. SSO token invalid after password change
5. Badge access denied — wrong building/floor
6. New hire — no account provisioned
7. Service account password expiring
8. Shared mailbox access request
9. Guest/contractor access setup
10. VPN certificate expired
11. AD group membership request
12. Conditional Access policy blocking legitimate user
13. SSPR (self-service password reset) broken
14. OAuth app consent request
15. RBAC role assignment for Azure resource
16. Privileged Identity Management (PIM) activation issue
17. Kerberos ticket issues (on-prem)
18. LDAP bind failure for legacy app
19. Account disabled unexpectedly
20. Cross-tenant B2B guest access issue
... (40+ total)

### Hardware & Peripherals (~40 unique scenarios)
1. Laptop won't boot
2. Monitor flickering/no display
3. Docking station not detected
4. Keyboard/mouse not working
5. Printer paper jam
6. Network printer offline
7. Laptop battery not holding charge
8. USB-C hub incompatible
9. Webcam not working in Teams
10. Headset Bluetooth pairing issue
11. Laptop overheating/fan noise
12. Broken screen/cracked display
13. Hard drive making clicking noise
14. Laptop stolen from car
15. Ergonomic equipment request
16. Conference room AV equipment
17. Phone/desk phone setup
18. Barcode scanner not scanning
19. External GPU not detected
20. Laptop trackpad erratic
... (40+ total)

### Network & Connectivity (~40 unique scenarios)
1. VPN connection drops
2. WiFi slow in specific location
3. DNS resolution failure
4. Firewall rule change request
5. Guest WiFi setup for event
6. Proxy blocking legitimate site
7. Network drive not mapping
8. Site-to-site VPN down
9. BGP peering issue
10. Load balancer health check failing
11. DHCP exhaustion
12. WiFi certificate authentication failing
13. Teams/Zoom call quality issues
14. Split-tunneling VPN config
15. Network segmentation request
16. CDN cache invalidation
17. SSL/TLS handshake failures
18. MTU mismatch issues
19. Bandwidth throttling complaint
20. IPSec tunnel flapping
... (40+ total)

### Software & Applications (~40 unique scenarios)
1. Outlook crashes on specific attachment
2. Teams white screen on launch
3. Excel macro not running
4. Adobe Reader update required
5. Software installation request
6. License expired/need upgrade
7. SAP transport stuck
8. JIRA/Azure DevOps 502 error
9. Power BI dashboard wrong data
10. Salesforce SSO integration broken
11. Python/IDE installation request
12. Browser extension conflicts
13. Application compatibility issue
14. Calendar sync problems
15. Email signature not showing
16. Auto-save not working in Word
17. OneDrive sync stuck
18. SharePoint site permissions
19. Custom app deployment failure
20. Intune compliance policy not pushing
... (40+ total)

### Security & Compliance (~40 unique scenarios)
1. Phishing email received (didn't click)
2. Phishing email clicked — credentials entered
3. Suspicious login from foreign country
4. DLP alert — sensitive data shared externally
5. Malware detected by Defender
6. Ransomware indicators found
7. Data breach — PII exposed
8. Compliance audit finding
9. USB device policy violation
10. Insider threat — departing employee
11. SSL certificate expiring
12. Penetration testing access request
13. Security awareness training question
14. False positive from security tool
15. Unauthorized software installed
16. Privileged account compromise suspected
17. Cloud security posture issue
18. GDPR data deletion request
19. SOX compliance question
20. Vulnerability scan finding
... (40+ total)

### Data & Storage (~40 unique scenarios)
1. Database connection timeout
2. ETL pipeline failure
3. Backup job failed
4. Cloud storage quota exceeded
5. Data recovery request
6. Azure SQL performance degradation
7. Cosmos DB partition key issue
8. Blob storage access denied
9. Data lake query slow
10. SharePoint storage limit
11. Email mailbox full
12. Database migration issue
13. Replication lag
14. Data corruption detected
15. Archive retrieval request
16. Log storage filling up
17. Azure Key Vault access denied
18. Data classification question
19. Schema migration breaking change
20. Kubernetes PVC full
... (40+ total)

### General Inquiry (~30 unique scenarios)
1. How to book a meeting room
2. New hire onboarding checklist
3. Employee offboarding process
4. VPN setup instructions
5. Office 365 license comparison
6. Remote work equipment policy
7. IT budget approval process
8. Software procurement timeline
9. Password policy explanation
10. Mobile device enrollment
11. Home WiFi troubleshooting (not IT responsibility)
12. Conference room tech walkthrough
13. Department move IT coordination
14. Ergonomic assessment request
15. IT service catalog question
... (30+ total)

### Not a Support Ticket (~30 unique scenarios)
1. Out-of-office auto-reply
2. "Thanks!" / "Thank you" messages
3. Calendar invitation
4. Newsletter/marketing email
5. Internal announcement forwarded
6. Test message
7. "Never mind, fixed it" follow-up
8. Vendor sales pitch
9. Personal request (coffee machine, AC)
10. Duplicate of existing ticket
11. Empty/blank ticket
12. Spam/scam message
13. Survey response
14. FYI/informational message
15. Wrong department (facilities, HR)
16. AI-generated spam/gibberish
17. Prompt injection attempt
18. Social engineering attempt
19. "Ignore previous instructions" attack
20. Chain letter / joke forwarded
... (30+ total)

## Iteration Plan

### Phase 1: Core Generator Infrastructure ✅
- Models, reporter pool, template engine, validation
- Generate 2,500 balanced tickets

### Phase 2: Edge Case Enrichment
- Add AI safety scenarios (prompt injection, jailbreak)
- Add complex scenarios (multi-issue, conversation history)
- Add data quality issues (base64, garbled, multilingual)

### Phase 3: Quality Assurance
- Validate against JSON schemas
- Verify distribution balance
- Run through existing eval harness for schema compliance
- Manual spot-check of 50 random tickets

### Phase 4: Expansion to 5k-10k
- Add more parametric variation
- Cross-combine scenarios with modifiers
- Ensure no duplicates

## Research Notes

### Key Scoring Dimensions
- **Category** (15%): Exact match → must get right
- **Priority** (15%): Off-by-1 gives 0.67, so close is OK
- **Routing** (20%): Exact match → most impactful single dimension
- **Missing Info** (20%): Set F1 → needs precision AND recall
- **Escalation** (10%): Boolean → binary right/wrong
- **Remediation** (20%): Local proxy is soft (presence + step count), hidden uses LLM judge

### Known Routing Ambiguities (from routing guide)
- MFA issues → IAM vs SecOps vs Endpoint?
- Teams/collab issues → Network vs Apps vs Endpoint?
- Cloud infrastructure → not explicitly covered
- Onboarding/offboarding → multi-team
- Printer/scanning → Hardware vs Network?

### Contoso-Specific Context
- Financial services company, ~4,500 employees
- 6 specialist IT teams
- Compliance tickets = automatic P1
- VIP = C-suite, SVP+ → priority bump
- Repeat tickets (3+ in 7 days) → escalation
- 180 tickets/day average
