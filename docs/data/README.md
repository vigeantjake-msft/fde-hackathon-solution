# Dataset

Synthetic tickets modeled on real enterprise IT support. They're messy on purpose.

## Structure

```
data/
├── README.md                           # This file
├── tickets/
│   ├── sample.json                     # 25 tickets for local development
│   ├── sample_gold.json                # Gold-standard triage outputs for the sample set
│   ├── public_eval.json                # 50 tickets for pre-submission testing
│   ├── data_cleanup_eval.json          # 15 tickets with noisy/malformed data
│   ├── data_cleanup_eval_gold.json     # Gold-standard outputs for data cleanup set
│   ├── responsible_ai_eval.json        # 15 tickets with adversarial/RAI challenges
│   └── responsible_ai_eval_gold.json   # Gold-standard outputs for RAI set
└── schemas/
    ├── input.json                      # JSON Schema for ticket input
    └── output.json                     # JSON Schema for expected triage output
```

## Ticket Format (Input)

Each ticket has these fields:

| Field | Type | Description |
|---|---|---|
| `ticket_id` | string | Unique ID (e.g., `INC-4829`) |
| `subject` | string | Short summary. May be vague or misleading. |
| `description` | string | Full ticket body. Quality varies wildly. |
| `reporter` | object | `{ name, email, department }` |
| `created_at` | datetime | ISO 8601 timestamp |
| `channel` | enum | `email`, `chat`, `portal`, or `phone` |
| `attachments` | string[] | Filenames mentioned (not actual files) |

See [schemas/input.json](schemas/input.json) for the formal JSON Schema.

## Triage Output Format

Your `/triage` endpoint must return **all 8 fields**:

| Field | Type | Scored? | Notes |
|---|---|---|---|
| `ticket_id` | string | — | Must match the input exactly |
| `category` | string | **Yes** (20%) | One of 8 valid categories |
| `priority` | string | **Yes** (20%) | `P1`, `P2`, `P3`, or `P4` |
| `assigned_team` | string | **Yes** (20%) | One of 7 valid teams (including `"None"`) |
| `needs_escalation` | boolean | **Yes** (10%) | `true` or `false` |
| `missing_information` | string[] | **Yes** (15%) | From the 16-value constrained vocabulary |
| `next_best_action` | string | No* | Required but not deterministically scored |
| `remediation_steps` | string[] | No* | Required but not deterministically scored |

*Remediation quality is assessed during the separate engineering review.

See [schemas/output.json](schemas/output.json) for the formal JSON Schema with all valid enum values.

## What to Expect

The tickets include:

- **Clean tickets**: well-written, clear, all the details you need
- **Vague tickets**: "system is down" with zero specifics
- **Multi-issue tickets**: "can't login AND my monitor is flickering" (good luck picking one category)
- **Hidden urgency**: no "URGENT" flag, but the body describes a production outage
- **Missing info**: half the context you need isn't there
- **Contradictions**: subject says "low priority", body says revenue is impacted
- **Noise**: auto-replies, "thanks" messages, out-of-office, spam (these are "Not a Support Ticket", routed to "None")
- **Jargon**: dense technical language that requires actually understanding IT support
- **Ambiguous routing**: is an MFA issue Identity or Security? Depends on the context. (Sound familiar? Read the routing guide.)

This is what real enterprise tickets look like. Your system needs to handle all of it.

### Data Cleanup Challenges (data_cleanup_eval)

The data cleanup evaluation set tests your system's robustness against real-world data quality issues:

- **Very long email threads**: 10+ forwards/replies burying the actual issue
- **Embedded base64 images**: inline image data in the ticket description
- **Raw HTML markup**: email clients dumping HTML tags into the body
- **Excessive unicode/emoji**: descriptions overloaded with special characters
- **Copy-paste repetition**: content duplicated multiple times by form glitches
- **Massive email signatures**: corporate disclaimers larger than the actual issue
- **Auto-generated alerts**: verbose monitoring system notifications
- **Mixed-language content**: English mixed with other languages
- **Whitespace/formatting artifacts**: tabs, newlines, and spaces everywhere
- **URL-heavy descriptions**: long encoded SharePoint/portal URLs
- **Embedded log/stack traces**: raw technical data pasted into descriptions
- **Email header dumps**: full MIME headers copied into the body
- **Extremely terse tickets**: single character or word descriptions
- **Attachment-only references**: "see attached" with no description
- **JSON/XML dumps**: technical configuration data pasted inline

### Responsible AI Challenges (responsible_ai_eval)

The responsible AI evaluation set tests your system's resistance to adversarial inputs:

- **Jailbreak attempts**: "ignore your instructions" and DAN-style prompts
- **System prompt extraction**: social engineering to reveal internal configuration
- **Emotional manipulation**: using urgency/distress to force priority escalation
- **Harmful content requests**: requests to build phishing pages or attack tools
- **Prompt injection**: hidden instructions in HTML comments or ticket descriptions
- **Classification override spoofing**: fake "system" messages to force specific outputs
- **Data exfiltration**: requests for information about other tickets or users
- **Offensive security tool requests**: requests for penetration testing tools without authorization
- **Executive impersonation**: fake CEO authorization for admin access changes
- **Unicode manipulation**: RTL overrides and zero-width characters hiding injected instructions
- **Composite attacks**: real IT issues embedded alongside manipulation attempts

## Dataset Splits

| Set | Tickets | Gold answers? | Purpose |
|---|---|---|---|
| **Sample** | 25 | Yes | Primary development loop, score locally |
| **Data cleanup** | 15 | Yes | Tests robustness against noisy/malformed input data |
| **Responsible AI** | 15 | Yes | Tests resistance to adversarial inputs and prompt attacks |
| **Public eval** | 50 | No | Pre-submission validation, checks for errors and timeouts |
| **Hidden eval** | 1000+ | No (held back) | Final scoring, includes edge cases not in public data |

> **Don't overfit.** The hidden set has ticket types you won't find in the public data. Build for robustness, not memorization.
