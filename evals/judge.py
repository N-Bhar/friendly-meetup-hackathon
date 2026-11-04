"""LLM-as-judge: a second model grades each answer against rubric.md."""

from pathlib import Path

from agent.llm import client_for

RUBRIC = (Path(__file__).parent / "rubric.md").read_text()


def judge(case: dict, result: dict) -> dict | None:
    """Return {"score": 1-5, "passed": bool, "reason": "..."}, or None to skip."""
    if not case.get("expected"):
        return None

    # TODO (Level 3):
    # 1. Build a prompt from RUBRIC, case["input"], case["expected"] and result["answer"].
    # 2. Call the judge model:  client, model = client_for("JUDGE")
    # 3. Ask for JSON back and parse it.  Hint: response_format={"type": "json_object"}
    # 4. Decide which scores count as a pass.
    return None
