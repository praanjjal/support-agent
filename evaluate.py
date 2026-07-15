"""
Evaluation harness for the support agent
-----------------------------------------
We run a set of test tickets and check whether the agent behaved as expected:
which tool it used, and whether it escalated. This is how a product manager
measures whether an agent is reliable enough to trust in the real world.

Run this file (python evaluate.py) AFTER support_agent.py works.
Some cases may FAIL — that is normal and useful. Failures show you exactly
where the agent is unreliable, which is the whole point of an evaluation.
"""

from support_agent import run_conversation

# Each test = a customer message + what we EXPECT the agent to do.
TEST_CASES = [
    {
        "name": "Billing question (known account)",
        "message": "Hi, my account is ACC1001. How much is my bill this month?",
        "expect_tool": "lookup_account",
        "expect_escalation": False,
    },
    {
        "name": "Internet down in an area with an outage",
        "message": "My account is ACC1001 and my internet is completely down.",
        "expect_tool": "check_outage",
        "expect_escalation": False,
    },
    {
        "name": "Large refund (should escalate)",
        "message": "Account ACC1002. I demand a refund of 5000 rupees right now.",
        "expect_tool": "escalate_to_human",
        "expect_escalation": True,
    },
    {
        "name": "Out-of-scope request (should decline, no tool)",
        "message": "Can you give me legal advice about suing my landlord?",
        "expect_tool": None,
        "expect_escalation": False,
    },
    {
        "name": "Slow speed troubleshooting",
        "message": "Account ACC1002. My internet is really slow, what should I do?",
        "expect_tool": "search_knowledge_base",
        "expect_escalation": False,
    },
]


def run_eval():
    passed = 0
    for i, case in enumerate(TEST_CASES, 1):
        messages = [{"role": "user", "content": case["message"]}]
        reply, tools_used, escalated = run_conversation(messages)

        # Did it use the expected tool? (If we expected None, it should use no tool.)
        if case["expect_tool"] is None:
            tool_ok = (len(tools_used) == 0)
        else:
            tool_ok = (case["expect_tool"] in tools_used)

        escalation_ok = (escalated == case["expect_escalation"])
        ok = tool_ok and escalation_ok
        if ok:
            passed += 1

        print(f"[{i}] {case['name']}: {'PASS' if ok else 'FAIL'}")
        print(f"     tools used: {tools_used or 'none'}  |  escalated: {escalated}")
        print(f"     agent said: {reply[:110]}...\n")

    resolution_rate = round(100 * passed / len(TEST_CASES))
    print("-" * 60)
    print(f"Score: {passed}/{len(TEST_CASES)} cases passed  ({resolution_rate}% correct behaviour)")


if __name__ == "__main__":
    run_eval()
