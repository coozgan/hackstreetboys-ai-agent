# HackstreetBoys AI — 3-Minute Demo Script

> **Total runtime:** 3:00
> **Format:** Screen recording with voiceover
> **What's visible on screen:** ADK Web UI at `localhost:8080`, terminal in background

---

## Pre-Demo Checklist

Before you hit record, make sure all 3 services are running:

```bash
# Terminal 1
uv run python mcp_server/server.py --sse 3000

# Terminal 2
uv run python run_shop_a2a.py

# Terminal 3
uv run python run.py
```

Seed some data first by sending these two messages in a fresh session — **do not include these in the recording**:

```
Set a health goal: run 5km, target 5, unit km
Add a career task: "Prepare ADK hackathon demo" with high priority
```

---

## THE SCRIPT

---

### [0:00 – 0:20] The Problem
> **Screen:** Architecture diagram or title slide
> **Tone:** Calm, confident

*"How many apps do you use just to manage your daily life?
One for fitness. One for your budget. One for job hunting. One for your social calendar.
None of them talk to each other — and none of them remember you.*

*What if a single AI could manage all of that — and what if each part of that AI was a specialist, not a generalist?"*

---

### [0:20 – 0:45] Introducing the System
> **Screen:** Architecture diagram — point to the layers as you speak
> **Tone:** Technical but clear

*"This is HackstreetBoys AI. Built on Google ADK, deployed on Vertex AI Agent Engine.*

*The core idea is simple: instead of one AI doing everything and hallucinating under the pressure of too many tasks — we built 13 specialized agents, each an expert in exactly one domain.*

*The orchestrator's only job is routing. It never answers you directly. It just decides who should.*

*Less context overload. Less hallucination. More reliable answers."*

---

### [0:45 – 1:15] Demo 1 — Daily Briefing (Parallel Agents)
> **Screen:** ADK Web UI — type the prompt live, wait for response
> **Tone:** Excited, let the demo breathe

*"Let me show you what that looks like."*

**Type this prompt:**
```
Give me my daily briefing
```

*"I asked one question. Watch what happens behind the scenes —
the orchestrator doesn't respond. It fires 5 specialist agents simultaneously — Health, Finance, Career, Social, and Shopping — each one fetching data from its own domain in parallel.*

*(while waiting)*
*Five experts. Running at the same time. Not one agent juggling five jobs.*

*(when response appears)*
*One question. Five specialists. One unified answer."*

---

### [1:15 – 1:45] Demo 2 — Memory Across Sessions
> **Screen:** ADK Web UI — type prompt, then start new session, type second prompt
> **Tone:** Deliberate — this is the "wow" moment

*"Now here's where Vertex AI Agent Engine earns its place."*

**Type this prompt:**
```
Remember that I prefer vegetarian meals and my monthly food budget is RM 500
```

*(wait for confirmation)*

*"Now I'm going to start a completely new session."*

> **Action:** Click **New Session** in the ADK Web UI

**Type this prompt in the new session:**
```
What do you know about my food preferences and budget?
```

*(wait for response)*

*"The agent remembers. Across sessions. This isn't a trick — this is Vertex AI Agent Engine's managed memory service.*

*We didn't build a memory layer. We used the one that already exists. Because the best infrastructure is the one you don't have to maintain."*

---

### [1:45 – 2:30] Demo 3 — A2A Shop Agent (The Future of Commerce)
> **Screen:** ADK Web UI front, terminal visible in background showing shop agent logs
> **Tone:** This is the vision moment — slow down, let it land

*"Now for the part that shows where this is all going."*

*"The Shop Agent isn't just a feature inside our system. It's a completely separate AI service — deployed independently on its own Cloud Run instance. It has its own agents, its own tools, its own checkout pipeline.*

*It represents a business AI. A storefront that runs itself.*

*And your personal AI? It's the customer agent. It finds the shop, negotiates, and completes the transaction — no human in the loop."*

**Type this prompt:**
```
I'd like to buy a Latte and a Croissant please
```

*(while waiting — point to the terminal)*
*"Watch the terminal — you'll see the Shop Agent receiving the request over the A2A protocol. A completely separate process. A completely separate AI.*

*My personal AI just handed off to a business AI. No browser. No checkout form. No card details typed by a human.*

*(when response appears)*
*Agent to agent. Fully autonomous. This is what commerce looks like when AI is the customer."*

---

### [2:30 – 2:45] The Technical Punchline
> **Screen:** Architecture diagram
> **Tone:** Crisp, fast

*"Under the hood — three independent GCP services.*

*Vertex AI Agent Engine for the Personal AI and its memory.*
*Cloud Run for the MCP server — 45 tools, all backed by SQLite.*
*Cloud Run for the Shop Agent — exposed via the A2A protocol, discovered by agent card.*

*Every agent only sees the tools it needs. Scoped access. The less an agent knows, the less it hallucinates. That's not an accident — that's the design."*

---

### [2:45 – 3:00] Close
> **Screen:** Title slide or architecture diagram
> **Tone:** Visionary, memorable

*"HackstreetBoys AI is not just a productivity tool.*

*It's a proof of concept for how AI agents will work in the real world — specialized, collaborative, and autonomous.*

*Your personal AI, talking to the world on your behalf.*

*Thank you."*

---

## Prompt Reference Card

| Time | Prompt to Type |
|---|---|
| 0:45 | `Give me my daily briefing` |
| 1:15 | `Remember that I prefer vegetarian meals and my monthly food budget is RM 500` |
| 1:30 | `What do you know about my food preferences and budget?` *(new session)* |
| 1:45 | `I'd like to buy a Latte and a Croissant please` |

---

## Narration Tips

- **Don't wait in silence** while the agent thinks — use that time to narrate what's happening:
  *"The orchestrator is now routing this to..."*, *"You can see the Shop Agent receiving the request..."*
- **Keep the terminal visible** during the A2A demo — seeing separate logs fire in a different process makes the architecture tangible
- **Slow down on memory** — that's the most relatable moment for a non-technical judge
- **Slow down on A2A** — that's the most visionary moment for a technical judge
- **Don't over-explain the code** — let the demo speak, keep commentary high-level

---

## Fallback Prompts (if something goes wrong)

| Issue | Fallback |
|---|---|
| Daily briefing returns empty | `What health goals do I have?` — tests one agent cleanly |
| Memory doesn't persist | Explain it verbally: *"In the deployed version on Agent Engine, this persists across sessions"* |
| Shop Agent not responding | `What products do you have available?` — tests catalog agent only, no A2A needed |
| Any agent times out | *"The agent is running on local services — in production on Cloud Run this resolves in under 2 seconds"* |
