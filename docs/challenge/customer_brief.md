# Mission Briefing

> ⚡ PRIORITY TRANSMISSION — Contoso Deep Space Station (CDSS) — Relayed to FDE Mission Support Team via subspace channel 7.

---

**From:** Commander Priya Kapoor, Station Ops Director, Contoso Deep Space Station
**To:** Microsoft FDE Mission Support Team
**Stardate:** March 2026
**Subject:** Help us fix our signal triage — people are going to die

---

## Who we are

Contoso Deep Space Station. ~2,000 crew aboard a research outpost parked 0.3 AU from Earth. We run deep-space sensor arrays, exobiology research, long-range communications relay, and a surprisingly competitive zero-gravity cricket league. Regulated by Terran Space Authority — containment protocols matter, hull breaches are expensive, and our crew are impatient (especially the ones who haven't had correctly flavored protein cubes in six weeks).

## What's broken

Our Mission Ops desk handles ~180 signals per day. Right now, a human ops officer reads every signal, decides what it is, assigns a priority, and routes it to one of our 6 specialist teams. It takes **3.4 hours on average** to get a signal to the right team. That's before anyone even starts working on it.

In space, 3.4 hours is the difference between "minor atmospheric imbalance" and "Deck 7 is now a vacuum." The Titan Outpost had a time-to-route of 2.8 hours. We all know what happened to the Titan Outpost.

**42% of signals get misrouted at least once.** When a signal lands with the wrong team, they bounce it back, and we start over. Some signals take 2–3 bounces before they reach the right crew. Last month, a contamination alert bounced between Spacecraft Systems and Deep Space Comms for six hours while the biohazard quietly did what biohazards do. Six. Hours. Every bounce adds a 4-minute light delay for confirmation. I have done the math. It is not good math.

The worst part: our ops officers spend so much time triaging that they can't do actual resolution work. They're basically expensive human routers floating in space. Very talented, very frustrated, very caffeinated humans — and the nutrient synthesizer keeps dispensing the wrong flavor protein cube, so morale is exactly where you'd expect. I could replace them with a particularly motivated houseplant — and we actually have one of those, because three specimens escaped from the Exobiology Lab during Q2 crew rotation, we caught two, and the third adapted. It lives in the hydroponics bay now. It does not route signals, but it has better judgment than some of my crew.

## What we want

We want to **automate first-pass triage** for every incoming signal. Specifically:

1. **Classify** the signal into the right category — what kind of anomaly is this?
2. **Set priority** — how urgent is this, really? (Crew write "URGENT" on everything. Someone once filed a Red Alert because the nutrient synthesizer was dispensing vanilla protein cubes instead of chocolate. We responded in full containment gear. I will never live that down. The quiet signal about oxygen recycler output dropping 3% on Deck 12? That was the actual emergency.)
3. **Route** to the correct specialist team — get it right the first time, because the second time might be too late. Or there won't be a second time.
4. **Flag what's missing** — half our signals don't include basic info we need. We waste time pinging the reporter back across subspace to ask "which subsystem?" or "what was the anomaly readout?" — and every round trip has a 4-minute light delay, so playing twenty questions takes literal hours
5. **Give our ops officers a head start on remediation** — even if a human still resolves the signal, tell them what to try first. Something more useful than "investigate the anomaly," which is the ops equivalent of saying "have you tried looking at the problem?"

## Our teams

We have 6 specialist operations teams:

| Team | What they handle |
|---|---|
| **Crew Identity & Airlock Control** | Biometric access, crew identity, profile provisioning, BioScan ID, directory sync |
| **Spacecraft Systems Engineering** | Workstations, hull-mounted systems, mobile devices, ShipOS issues, ShipOS MDM, peripherals |
| **Deep Space Communications** | Subspace relay, local comms mesh, DNS beacons, signal routing, proxy, inter-deck links |
| **Mission Software Operations** | Mission apps (navigation suite, sensor platforms, astro-lab tools, internal tools), licensing, integrations |
| **Threat Response Command** | Hostile contact, contamination, anomalous readings, data breaches, containment protocol incidents, certificate management |
| **Telemetry & Data Core** | Data cores, crew file stores, sensor archives, backups, data access requests, telemetry pipelines |

I've attached our **internal routing guide** — but fair warning, it was written 8 months ago and some things have changed. We've also reorganized since the Q2 crew rotation. About 20% of signal types aren't covered in it, and some of the routing rules overlap between teams. My team leads argue about ownership constantly. For example: who handles biometric scan failures — Crew Identity or Threat Response? Depends on the context, and honestly we're not consistent about it ourselves.

## What "good" looks like to us

- **Reduce misrouting from 42% to under 15%** in the first month. Anything above 30% and I start getting memos from Station Command with phrases like "unacceptable" and "reviewing leadership decisions."
- **Time-to-route under 5 minutes** (from 3.4 hours — in space, 3.4 hours is enough time for a contained leak to become an uncontained one)
- **Catch missing information proactively** so we stop playing subspace ping-pong with reporters. Every back-and-forth adds 8 minutes of light delay plus however long it takes the reporter to notice they have a message, which on the night shift is approximately "until their coffee runs out"
- **Actionable remediation steps** — not generic "investigate the anomaly" but specific things an ops officer can actually try before someone freezes to death. Or boils. We've had both.

If you can show me this working on even 50 of our real signals, I can make the case to Station Command. And believe me, Station Command takes a lot of convincing. They're still not over the protein cube incident.

## Things you should know

- Our signals come in through **4 channels**: subspace relay (long-form reports from people who had time to think), holodeck comm (quick crew chatter, often filed while floating upside down), the bridge terminal (self-service kiosk — the form fields are treated as creative suggestions), and emergency beacon (transcribed by the duty officer — usually panicked, garbled, and occasionally just someone breathing heavily into the comm for thirty seconds before a cryo-sleep auto-reply kicks in). Quality varies wildly. Subspace relay signals tend to be longer. Holodeck comms are short and missing context. Emergency beacon transcriptions are the kind of thing you read with one hand on the containment alarm.
- **Some signals aren't real incidents** — we get auto-replies, "thanks" messages, cryo-sleep out-of-rotation notifications ("I am currently in suspended animation and will return your signal in 6–18 months"), and occasional junk transmissions from that merchant vessel that keeps trying to sell us "premium hull sealant." Our system doesn't filter these before routing, so our highly trained ops officers get to manually triage interstellar static.
- **We run the station stack**: BioScan ID for biometrics with BioAuth panels at every airlock, ShipOS MDM for device management, Mission Suite for crew productivity, FlightOS for navigation and flight control, Station Core for compute and storage, and SubComm for inter-deck and external communications. Most of our infrastructure runs on Station Core. We recently deployed SentinelGrid for threat detection and certificate monitoring. We still have some legacy modules — like the legacy atmospheric processors from the original build and a few isolated sensor archives that predate the station refit.
- **Priority is subjective**: Crew over-escalate constantly. "URGENT" in the subject line usually means "I'm mildly inconvenienced and haven't had coffee." But sometimes a quiet signal like "slight variance in oxygen recycler output" is actually Red Alert material, and the person filing it is too calm because they don't realize they're slowly suffocating. Context matters more than keywords. Exclamation points are inversely correlated with actual danger. The protein cube incident was filed as P1 Red Alert. The actual hull micro-fracture on Deck 4 was filed as P3 with the subject line "small draft in corridor."
- **Containment signals are special**: Anything involving potential hull breach, atmospheric compromise, or unauthorized access to restricted decks must be escalated to Threat Response Command immediately, regardless of category. Getting this wrong has consequences. Fatal ones. The kind that end up in the station's permanent record with a black border around the entry.

## One more thing

I don't need a chatbot. I don't need a holographic dashboard. I definitely don't need another "AI-powered insights platform" that takes 45 seconds to tell me what any ops officer could figure out in 3. I need **an API I can plug into our existing bridge terminal workflow** that returns a JSON decision for each signal. Fast, reliable, and right most of the time. If it's not sure, it should say so — confident and wrong is worse than uncertain and honest when there's vacuum on the other side of the hull.

We are 0.3 AU from the nearest competent help. My patience is approximately the same distance from running out.

— Commander Kapoor

*P.S. — If your system routes a hull breach signal to Mission Software Operations, I will find you. Metaphorically. Across 0.3 AU. It'll take a while but I'm patient.*
