# PRD: Autonomous Customer Support Agent (Broadband)

**Author:** Pranjal Patil
**Status:** v1- prototype complete
**Last updated:** July 2026

> *Note for reviewers: this documents a working prototype that studies the agent pattern behind enterprise platforms like Salesforce Agentforce. All metrics are measured on a controlled test set with mock data, not production, called out explicitly in Section 5.*

---

## 1. Summary

An AI support agent for a home-broadband provider that resolves customer requests end to end. Given a plain-language message, the agent infers intent, autonomously chains the tool calls needed to gather context and act, and then either resolves the issue itself or hands off to a human, always within defined safety guardrails. The distinguishing property is **agency**: the agent is never told which tools to use or in what order; it plans that sequence itself from the customer's message.

## 2. Problem & context

Broadband customers contact support for a predictable mix of issues, billing questions, outages, slow-speed troubleshooting, plan changes, and refund requests. Most require the same first steps every time: verify the customer, look up their account, check whether a known outage explains the problem, or pull the right troubleshooting article. Handling these routine, multi-step lookups manually is slow for the customer and low-value work for human agents, while a subset of requests (large refunds, anything outside broadband support) genuinely *needs* a human's judgment or authority.

The opportunity: automate the routine, multi-step resolutions safely, while reliably routing the rest to a human, without the agent ever overstepping its authority or acting on unverified identity.

## 3. Target users

**Primary- the broadband customer.** Wants their issue understood and resolved quickly, without repeating themselves or waiting in a queue for a routine lookup.

**Secondary- the human support agent.** Wants routine tickets handled automatically and only the genuinely hard or restricted cases escalated to them, arriving with context already gathered rather than from scratch.

The two goals are compatible: automating routine resolution serves the customer *and* frees the human for the cases that need them.

## 4. Goals & non-goals

**Goals**
- Resolve common broadband support requests end to end without a human.
- Escalate safely and with context whenever the agent hits a guardrail or lacks confidence.
- Never act unsafely: no account disclosure without identity verification, no action beyond the agent's defined authority.

**Non-goals (explicitly out of scope for v1)**
- **No persistence.** Tickets and conversations are not stored across sessions; ticket IDs are generated for the flow, not saved to a real system.
- **No real backend.** Runs against mock CRM, outage, and knowledge-base data, not a live database.
- **No confidence scoring.** Escalation is rule-based (thresholds and guardrails), not driven by a learned confidence signal.
- **No multi-language / no voice.** Text, single language, reactive only, the agent does not do proactive outreach.

Stating these keeps the prototype honest about what it does and doesn't prove.

## 5. Success metrics

**Primary metric- correct-action rate.** The share of test scenarios in which the agent took the *correct action*, defined as: (a) it used the expected tool for the scenario, **and** (b) its escalation behavior matched what was expected (escalated when it should, didn't when it shouldn't).

The metric deliberately scores **actions, not words**. A support agent that says the right thing but fails to *do* it (e.g. verbally refuses a refund but never notifies a human) has failed, and a response-only check would miss that. This choice is the core of the evaluation design.

- **Result: 5/5 scenarios (100% correct-action rate)** on the test suite- up from an initial 80% (see Section 8).
- **Honest caveat:** this is measured on 5 representative scenarios against mock data. It demonstrates the pattern works on the covered cases; it is *not* a production reliability claim. Expanding the suite and validating on real traffic are explicit next steps.

## 6. Functional requirements

### 6.1 Intent understanding
From a single plain-language message, the agent classifies intent into: billing, outage, troubleshooting, plan change, refund, or out-of-scope, then plans its tool use accordingly.

### 6.2 Tools (actions the agent may take)
| Tool | Purpose |
|---|---|
| `lookup_account` | Retrieve plan, bill, balance, and service area by account ID |
| `check_outage` | Check whether a known outage covers the customer's area |
| `search_knowledge_base` | Retrieve troubleshooting or policy steps |
| `create_ticket` | Open a ticket when an issue can't be resolved immediately |
| `escalate_to_human` | Hand off to a human with a summary of what was already tried |

The agent chains these on its own- e.g. for "my internet is down," it calls `lookup_account` to find the service area, then `check_outage` on that area, without being told to.

### 6.3 Guardrails (safety requirements)
- **Identity verification.** The agent must not disclose account details until the customer provides an account ID.
- **Authority limit.** The agent may not approve refunds or payments above 1,000 rupees on its own; such requests *must* trigger `escalate_to_human`.
- **Out-of-scope refusal.** Requests outside broadband support (e.g. legal, medical) are declined rather than attempted.
- **Low-confidence escalation.** When unsure it can resolve an issue, the agent escalates rather than guessing.

### 6.4 Human-in-the-loop escalation
Escalation is an explicit tool call, not just a verbal refusal. Every hand-off carries a reason and a summary of what the agent already tried, so the human starts with context rather than from zero.

## 7. Primary user flow

1. Customer sends a request in plain language.
2. Agent applies the identity guardrail (no account data without an account ID).
3. Agent infers intent and plans which tools to call.
4. Agent executes and chains tool calls, reading each result to decide the next step.
5. Agent resolves within its authority **or** calls `escalate_to_human` with a summary.

*Worked example:* Customer: "My account is ACC1001, my internet is down." -> Agent calls `lookup_account` (finds area = Mumbai-West) -> calls `check_outage` (finds an active fiber outage) -> replies that there's a known outage with an ETA, and that it isn't a fault on the customer's side. Two chained tool calls, planned by the agent from one sentence.

## 8. Key learning- what the evaluation caught

On the first evaluation run, the suite scored **80% (4/5)**. The failure was the large-refund case, and it was a **silent failure**: the agent correctly *refused* the 5,000-rupee refund in conversation, but never called `escalate_to_human`, so in a real deployment, no human would ever have been notified and the customer would be stuck. It said the right thing while failing to take the right action.

The fix was a requirements/instruction change, not a code change: tightening the guardrail from a vague "escalate those" to an explicit "you **must** call the `escalate_to_human` tool, refusing in words alone leaves the customer stuck." That took the suite from **80% to 100%**.

The takeaway, and the reason the eval scores actions rather than words, is that a plausible-sounding response can hide a real behavioral failure. For an agent that takes actions on a customer's behalf, action-level evaluation is what catches the failures that matter.

## 9. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Agent discloses account data to the wrong person | Identity-verification guardrail before any account action |
| Agent exceeds its authority (large refund) | Hard 1,000-rupee limit -> mandatory `escalate_to_human` |
| Agent improvises on out-of-scope requests | Explicit refusal behavior |
| Fluent-but-wrong actions pass unnoticed | Action-level evaluation instead of response-level |
| Metrics overstated | Results reported as test-set-only on mock data, not production |

## 10. Limitations & future work

- Add a real ticket store and cross-session conversation memory.
- Expand the evaluation set and track **escalation rate over time** as a trust metric.
- Replace rule-based escalation with **confidence scoring**, so hand-off decisions are data-driven.
- Validate on real traffic (e.g. shadow mode or A/B) before treating the correct-action rate as a production number.

---

## Appendix- Technical implementation (the *how*)

*Kept separate from the product spec above: this appendix is engineering detail, the kind that belongs in the README rather than the PRD.*

- **Language:** Python
- **Model:** an LLM with tool-calling (Anthropic Claude API)
- **Agent loop:** the model is called with the tool definitions; if it requests a tool, the matching Python function runs and the result is returned to the model, looping until the model produces a plain text reply (resolve or escalate).
- **Mock backends:** in-memory CRM (accounts), outage map, and knowledge base stand in for real systems.
- **Evaluation:** `evaluate.py` runs the test scenarios and checks, per case, which tool was used and whether escalation occurred- the action-level scoring described in Section 5.
