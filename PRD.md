# PRD: Autonomous Customer Support Agent

**Author:** Pranjal Patil
**Type:** Prototype / product exploration
**Status:** v1 complete (5/5 evaluation)

---

## 1. Problem

Customer support is dominated by high-volume, repetitive requests — billing questions, outage checks, basic troubleshooting. These tie up human agents on low-complexity work, slow down response times, and inflate cost per ticket. Traditional chatbots help only marginally: they follow rigid scripts, can't take action in backend systems, and hand every non-trivial case to a human anyway.

The opportunity is to move from a scripted chatbot to an **autonomous agent** that can actually resolve multi-step requests by using company systems, while safely escalating what it shouldn't handle alone.

## 2. Target users

- **Primary — Support operations lead:** wants higher deflection of routine tickets, faster resolution, and confidence the automation won't act recklessly.
- **Secondary — End customer:** wants a fast, correct answer without waiting in a queue for simple issues.
- **Tertiary — Human support agent:** wants to receive only the cases that genuinely need a human, with context already gathered.

## 3. Goals and non-goals

**Goals**
- Autonomously resolve common broadband support requests (billing, outage, troubleshooting).
- Escalate restricted or low-confidence cases to a human with a summary.
- Operate within explicit safety guardrails.
- Be measurable — every release is scored against a test suite.

**Non-goals (v1)**
- No live CRM/payment integration (uses a mock data layer).
- No cross-session memory or authentication system.
- Not tuned for scale or latency; this is a correctness-first prototype.

## 4. Solution overview

An LLM-driven agent with five tools (`lookup_account`, `check_outage`, `search_knowledge_base`, `create_ticket`, `escalate_to_human`). The agent reasons about intent, chains tool calls as needed, and returns a resolution or a human hand-off. Guardrails are enforced through explicit instructions: verify identity before sharing account data, escalate refunds above a threshold, and decline out-of-scope requests.

The value framing mirrors the industry shift in 2026 from *assistive* AI (suggests, waits for approval) to *autonomous* AI (acts within guardrails) — the same thesis behind Salesforce Agentforce.

## 5. Success metrics

| Metric | Why it matters | v1 result |
|--------|----------------|-----------|
| Resolution / correct-action rate | Core value: how often the agent does the right thing | 100% (5/5) |
| Escalation rate | Trust signal — too low is reckless, too high is useless | Escalates exactly the cases that require it |
| Silent-failure rate | Cases where it *says* the right thing but *does* the wrong thing | Driven to 0 after v1 fix |

In production I would additionally track deflection rate, CSAT, and time-to-resolution.

## 6. Key risk and how the eval surfaced it

The central risk with autonomous agents is a **plausible-but-wrong action** — output that reads correctly but fails to actually do the job. v1 exhibited exactly this: the agent verbally refused an out-of-policy refund but never triggered escalation, so no human would have been alerted. The evaluation caught a failure that a human reading the transcript would have approved. This is the argument for treating evaluation, not model choice, as the core PM lever for agent reliability.

## 7. Competitive landscape

- **Salesforce Agentforce** — autonomous agents native to CRM data; strongest where the customer already lives in Salesforce.
- **Zendesk AI / Intercom Fin** — support-centric agents layered on ticketing platforms; strong for support, narrower in scope.
- **Sierra, Decagon** — newer specialist customer-experience agent startups competing on resolution quality.

The differentiator across all of them is the same: depth of grounded customer data and the reliability of the guardrail/escalation layer — which is exactly what v1 is built to explore.

## 8. Next iteration

Add confidence-based escalation (data-driven rather than rule-based), a persistent ticket store and memory, and a larger evaluation set with escalation rate tracked over time as the primary trust KPI.
