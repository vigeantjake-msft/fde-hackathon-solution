# 🛰️ Be a Microsoft FDE for a Day

## What Is This

A **build challenge** where you tackle the kind of problem FDEs actually solve: Contoso Deep Space Station is drowning in mission ops signals — hull breaches going unrouted, containment alerts bouncing between wrong teams, and 2,000 crew members who think "URGENT" means "my nutrient synthesizer dispensed the wrong flavor protein cube." They need an AI-powered signal triage API. Yesterday. Commander Kapoor is not patient, and she is 0.3 AU away from anyone who can help.

You'll read their (messy, incomplete) mission briefing, dig through their signal data, build a real deployed API, and ship it. Then we score it against a hidden evaluation set you've never seen. The scoring computer has no feelings. It has no mercy. It is, in this regard, very much like outer space.

**This is not a chatbot challenge.** It's an engineering challenge. One endpoint, one JSON in, one JSON out, deployed and callable. The kind of thing you'd actually build for a station ops team before someone freezes to death. Or boils. They've had both.

## Getting Started

1. **Read the mission briefing** → [docs/challenge/customer_brief.md](docs/challenge/customer_brief.md). Understand the ops problem before you write code. People who skip the brief misroute signals. People who misroute signals end up in the Admiral's memos.
2. **Review the routing guide** → [docs/challenge/routing_guide.md](docs/challenge/routing_guide.md). Their internal (incomplete) routing rules. Chief Signal Officer Mehta's margin notes are worth reading.
3. **Read the challenge spec** → [docs/challenge/](docs/challenge/). API contract, schemas, scoring rubric — everything the scoring computer needs to judge you
4. **Explore the data** → [docs/data/](docs/data/). Synthetic mission ops signals for development and testing
5. **Test locally** → [docs/eval/](docs/eval/). Run the eval harness against your endpoint — same cold math as the platform
6. **Submit** → deploy, push, then go to **[aka.ms/fde/hackathon](https://aka.ms/fde/hackathon)** to submit. May the void be indifferent in your favor.

## Repository Structure

```
├── docs/
│   ├── challenge/       # Mission briefing, routing guide, scoring rubric
│   ├── data/            # Synthetic signal dataset + schemas
│   ├── eval/            # Public evaluation harness (run locally)
│   └── submission/      # How to submit your solution
├── py/                  # Python workspace (uv)
│   ├── common/libs/     # Provided common libraries (FastAPI, Pydantic models)
│   ├── libs/            # Your libraries
│   └── apps/            # Your applications
├── ts/                  # TypeScript workspace (pnpm)
│   ├── libs/            # Your libraries
│   └── apps/            # Your applications
└── infra/               # Infrastructure as Code (Pulumi + Azure)
    └── app/             # Your Pulumi program
```

## Development Environment

Work locally or in any cloud-hosted environment, your choice. A [devcontainer](.devcontainer/) is included if you want a pre-configured setup, but it's entirely optional. Unlike hull integrity, this one truly is optional.

Requirements: Python 3.12+, Node.js 22+, [uv](https://docs.astral.sh/uv/), [pnpm](https://pnpm.io/)

```bash
# Python
cd py && uv sync

# TypeScript
cd ts && pnpm install

# Pre-commit hooks
uvx pre-commit install
```

## Rules

- **One submission** per person. Make it count. Like airlock procedures.
- Any language, any framework, any AI model. Your call.
- Copilot, Cursor, Claude: all fair game. Use everything you've got. We are not above using robots to build robot helpers.
- Must be deployed and callable via HTTPS. Localhost is 0.3 AU away and nobody can reach it.
- Documentation is required. If you can't explain it, you didn't build it. Commander Kapoor reads everything.

## Evaluation

Your hidden-set **functional score** is **0–100**.

Functional scoring is deterministic: **macro F1** for classification and routing, **partial credit** for priority, **set F1** for missing info, **binary F1** for escalation. Plus latency and cost. No LLM judges. No vibes. Just math. Cold, unforgiving math — like the vacuum outside the viewport. See [docs/challenge/](docs/challenge/) for every detail.

Separately, we review repos for engineering quality: clean design, sensible tradeoffs, attention to latency and cost, real tests, and a system another engineer could trust. The kind of engineering that keeps 2,000 crew alive at 0.3 AU from Earth.

Final rankings use a **hidden evaluation set** with edge cases you haven't seen. Don't overfit to the public data. Build it like it's going to production tomorrow — because in space, "tomorrow" is when the next hull breach happens.

## Before You Submit

Your solution must:

- Be **deployed** and callable via HTTPS
- Pass `GET /health` with HTTP 200 (consider it a life-signs check)
- Accept `POST /triage` with the documented JSON schema
- Include `submission.json` with your endpoint URL and repo link
- Include three mandatory docs: `docs/architecture.md`, `docs/methodology.md`, `docs/evals.md`
- Have a clean, well-tested, well-documented **public repository**

See [docs/submission/](docs/submission/) for the full checklist, then submit at **[aka.ms/fde/hackathon](https://aka.ms/fde/hackathon)**.

## License

[MIT](LICENSE)
