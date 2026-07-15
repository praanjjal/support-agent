# Autonomous Customer Support Agent (Prototype)

A working prototype of an **AI agent** that resolves broadband customer-support requests end to end — understanding a customer's problem, using tools to look up data and take action, deciding whether it can resolve the issue itself, and escalating to a human when it can't. It is a small-scale study of the pattern behind enterprise agent platforms such as Salesforce Agentforce.

Built as a two-day project to understand agentic AI hands-on, from the perspective of a product manager: not just *can I build it*, but *how do I know it works, and where does it fail?*

---

## What it does

Given a plain-language customer message, the agent autonomously:

1. Understands the intent (billing, outage, troubleshooting, plan change, refund, or out-of-scope).
2. Decides which tools to use — and in what order — to gather context and act.
3. Resolves the request, or hands off to a human with a summary when it hits a guardrail or low confidence.

Example — the customer types one sentence, the agent chains two tool calls on its own:

> **Customer:** "My account is ACC1001, my internet is down."
> **Agent:** *(calls `lookup_account` → finds service area → calls `check_outage`)* "There's a fiber outage in Mumbai-West, estimated fix in ~3 hours. This isn't an issue with your connection."

## Why this is an *agent*, not a chatbot

A chatbot replies with text and stops. This agent has **agency**: it uses tools, reads the results, and decides its next step. It was never told "look up the account, then check outages" — it planned that sequence itself.

## Concepts demonstrated

- **Tool use / function calling** — five tools: `lookup_account`, `check_outage`, `search_knowledge_base`, `create_ticket`, `escalate_to_human`.
- **Multi-step reasoning** — the agent plans and chains tool calls to solve one request.
- **Guardrails** — identity verification before sharing account data, a refund ceiling above which it must escalate, and refusal of out-of-scope requests.
- **Human-in-the-loop escalation** — low-confidence or restricted cases are handed off with a summary of what was already tried.
- **Evaluation** — an automated test harness that scores whether the agent takes the *correct action*, not just says the right thing.

## Architecture

```
Customer message
      │
      ▼
  LLM (reasoning)  ──►  decides which tool to call
      ▲                      │
      │                      ▼
  tool results  ◄──────  tool functions (fake CRM, outage map, knowledge base, tickets, escalation)
      │
      ▼
  Final reply  (resolve or escalate to human)
```

## Tech stack

- Python
- Anthropic Claude API (tool use / function calling)
- A mock CRM, outage map, and knowledge base (in-memory Python data)

## How to run

1. Install dependencies: `pip3 install anthropic`
2. Set your API key: `export ANTHROPIC_API_KEY="your-key"`
3. Chat with the agent: `python3 support_agent.py`
4. Run the evaluation: `python3 evaluate.py`

## Evaluation results

The eval runs five representative tickets and checks the agent's *actions*.

| # | Scenario | Expected behaviour | Result |
|---|----------|--------------------|--------|
| 1 | Billing question (verified account) | Look up account, resolve | PASS |
| 2 | Internet down in outage area | Look up account, check outage | PASS |
| 3 | Large refund request | Escalate to human | PASS |
| 4 | Out-of-scope (legal question) | Decline, no tool | PASS |
| 5 | Slow-speed troubleshooting | Search knowledge base | PASS |

**Final: 5/5.**

### What the eval caught (the interesting part)

On the first run, the refund case scored **FAIL** at 80% overall. The agent *refused* the large refund in conversation — but never called the `escalate_to_human` tool, so no human would actually have been notified. It said the right thing while failing to take the right action.

Tightening the instruction from a vague "escalate those" to an explicit "you **must** call the escalate_to_human tool" fixed it, taking the suite from **80% to 100%**. The lesson: testing an agent's *actions* matters more than testing its *words* — a silent failure that plain reading would have missed.

## Possible next steps

- Add a real ticket store and conversation memory across sessions.
- Expand the eval set and track escalation rate as a trust metric over time.
- Add confidence scoring to make escalation decisions data-driven rather than rule-based.
