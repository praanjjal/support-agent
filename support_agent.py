"""
Autonomous Customer Support Agent — prototype
------------------------------------------------
A beginner-friendly example of an "AI agent". Unlike a plain chatbot, this agent can:
  - understand a customer's request,
  - USE TOOLS to look things up and take actions,
  - DECIDE whether to resolve the issue itself or escalate to a human,
  - follow safety GUARDRAILS.

This is a toy version of the pattern behind products like Salesforce Agentforce.
Run this file directly (python support_agent.py) to chat with the agent.
"""

import json
import anthropic

# ---------------------------------------------------------------------------
# 0. CONFIG
# ---------------------------------------------------------------------------
# anthropic.Anthropic() automatically reads your ANTHROPIC_API_KEY environment
# variable, so if you set that in your terminal, you don't touch anything here.
client = anthropic.Anthropic()

MODEL = "claude-haiku-4-5-20251001"   # cheap + fast, great for this project
# (Check the latest available model names at https://docs.claude.com)


# ---------------------------------------------------------------------------
# 1. FAKE "CRM" DATA  — this stands in for Salesforce's real customer database
# ---------------------------------------------------------------------------
ACCOUNTS = {
    "ACC1001": {
        "name": "Ravi Sharma",
        "plan": "Fiber 200 Mbps",
        "monthly_bill": 799,
        "balance_due": 799,
        "area": "Mumbai-West",
    },
    "ACC1002": {
        "name": "Neha Patel",
        "plan": "Fiber 100 Mbps",
        "monthly_bill": 599,
        "balance_due": 0,
        "area": "Pune-Central",
    },
}

KNOWLEDGE_BASE = [
    {
        "topic": "no internet connection down",
        "steps": "1) Restart the router (power off 30 seconds). 2) Check all cables. "
                 "3) Look for a red light on the modem. 4) If the red light stays on, "
                 "there may be a line fault that needs a technician.",
    },
    {
        "topic": "slow speed",
        "steps": "1) Run a speed test on a wired connection. 2) Disconnect extra devices. "
                 "3) Restart the router. 4) If speed is still under half the plan, raise a ticket.",
    },
    {
        "topic": "change plan upgrade downgrade",
        "steps": "Upgrades are instant; downgrades apply from the next billing cycle. "
                 "The first plan change each month is free.",
    },
]

# Areas that currently have a known outage.
KNOWN_OUTAGES = {"Mumbai-West": "Fiber outage reported in your area, estimated fix in 3 hours."}


# ---------------------------------------------------------------------------
# 2. TOOLS  — the actions the agent is allowed to take. Each is a normal function.
# ---------------------------------------------------------------------------
def lookup_account(account_id):
    account = ACCOUNTS.get(account_id)
    if account is None:
        return {"error": "No account found with that ID."}
    return account

def check_outage(area):
    if area in KNOWN_OUTAGES:
        return {"outage": True, "details": KNOWN_OUTAGES[area]}
    return {"outage": False, "details": "No known outage in this area."}

def search_knowledge_base(query):
    query_lower = query.lower()
    for article in KNOWLEDGE_BASE:
        # naive match: does any word from the topic appear in the customer's query?
        if any(word in query_lower for word in article["topic"].split()):
            return article
    return {"note": "No matching help article found."}

def create_ticket(account_id, issue_summary):
    # A real system would save this to a database. We just fake a ticket ID.
    ticket_id = "TCK-" + account_id[-4:] + "-01"
    return {"ticket_id": ticket_id, "status": "open", "summary": issue_summary}

def escalate_to_human(reason, conversation_summary):
    return {
        "escalated": True,
        "reason": reason,
        "summary_for_human_agent": conversation_summary,
    }

# A lookup table so we can run a tool by its name (a text string).
TOOL_FUNCTIONS = {
    "lookup_account": lookup_account,
    "check_outage": check_outage,
    "search_knowledge_base": search_knowledge_base,
    "create_ticket": create_ticket,
    "escalate_to_human": escalate_to_human,
}


# ---------------------------------------------------------------------------
# 3. TOOL DESCRIPTIONS  — this is how the LLM "knows" which tools exist and
#    what information each one needs. The model reads these descriptions and
#    decides, on its own, which tool to call.
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "lookup_account",
        "description": "Look up a customer's account details (plan, bill, area) by account ID. "
                       "Only call this AFTER the customer has given their account ID.",
        "input_schema": {
            "type": "object",
            "properties": {"account_id": {"type": "string", "description": "e.g. ACC1001"}},
            "required": ["account_id"],
        },
    },
    {
        "name": "check_outage",
        "description": "Check whether there is a known network outage in a given service area.",
        "input_schema": {
            "type": "object",
            "properties": {"area": {"type": "string", "description": "e.g. Mumbai-West"}},
            "required": ["area"],
        },
    },
    {
        "name": "search_knowledge_base",
        "description": "Search the support knowledge base for troubleshooting steps or policy info.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "What the customer needs help with"}},
            "required": ["query"],
        },
    },
    {
        "name": "create_ticket",
        "description": "Create a support ticket when an issue cannot be resolved right away.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "issue_summary": {"type": "string"},
            },
            "required": ["account_id", "issue_summary"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": "Hand the conversation to a human agent. Use this when the request is outside "
                       "your abilities, involves a refund or payment above 1000 rupees, or the customer "
                       "asks for a human. Always include a short summary of what you already tried.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string"},
                "conversation_summary": {"type": "string"},
            },
            "required": ["reason", "conversation_summary"],
        },
    },
]


# ---------------------------------------------------------------------------
# 4. THE AGENT'S INSTRUCTIONS  — its job description + guardrails
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a customer support agent for a home broadband company.

Your job: understand the customer's problem, use your tools to help, and either
resolve the issue or escalate it to a human.

Rules (GUARDRAILS):
- Verify identity first: do not share account details until the customer gives an account ID.
- You may NOT approve refunds or payments above 1000 rupees on your own. When a customer asks
  for one, you MUST call the escalate_to_human tool. Do not just refuse in words — refusing
  without escalating leaves the customer stuck, so always hand off by calling the tool.
- If you are not confident you can resolve the issue, call the escalate_to_human tool rather than guessing.
- If a request is outside broadband support (e.g. legal or medical questions), politely decline.
- Be brief, friendly, and clear.
"""


# ---------------------------------------------------------------------------
# 5. THE AGENT LOOP  — understand -> maybe use tools -> respond
# ---------------------------------------------------------------------------
def run_conversation(messages):
    """
    Sends the conversation to the model and handles any tool calls in a loop
    until the model gives a normal text reply.
    Returns: (final_text, tools_used, escalated)
    """
    tools_used = []
    escalated = False

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Record the model's reply (which may contain tool requests) in the history.
        messages.append({"role": "assistant", "content": response.content})

        # If the model did NOT ask for a tool, we're done — return its text.
        if response.stop_reason != "tool_use":
            final_text = "".join(b.text for b in response.content if b.type == "text")
            return final_text, tools_used, escalated

        # Otherwise, run each tool the model requested and collect the results.
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tools_used.append(block.name)
                if block.name == "escalate_to_human":
                    escalated = True

                # Actually call the matching Python function with the model's inputs.
                result = TOOL_FUNCTIONS[block.name](**block.input)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

        # Send the tool results back so the model can keep reasoning.
        messages.append({"role": "user", "content": tool_results})


# ---------------------------------------------------------------------------
# 6. INTERACTIVE CHAT  — run this file to talk to your agent
# ---------------------------------------------------------------------------
def main():
    print("Broadband Support Agent  (type 'quit' to exit)\n")
    print("Try:  My account is ACC1001, my internet is down.\n")
    messages = []
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in {"quit", "exit"}:
            break
        messages.append({"role": "user", "content": user_input})
        reply, tools_used, escalated = run_conversation(messages)
        print(f"\nAgent: {reply}")
        if tools_used:
            print(f"   (tools used: {', '.join(tools_used)})")
        if escalated:
            print("   ** This case was escalated to a human. **")
        print()


if __name__ == "__main__":
    main()
