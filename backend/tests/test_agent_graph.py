from __future__ import annotations

import pytest

from app.agent_graph import invoke_agent_graph, langgraph_available


pytestmark = pytest.mark.skipif(
    not langgraph_available(),
    reason="LangGraph dependency is not installed in this review runtime",
)


def _stages(*, fail_index: int | None = None):
    definitions = []
    for index in range(7):
        def handler(stage=index):
            if stage == fail_index:
                raise ValueError("isolated stage failure")
            return {"stage": stage + 1, "trusted": True}

        definitions.append((f"Agent {index + 1}", f"Responsibility {index + 1}", handler))
    return definitions


def _fallback_reasoner(name, responsibility, facts, preferred_provider):
    return (
        f"{name} explained verified stage {facts['stage']}.",
        {"mode": "FALLBACK", "provider": preferred_provider, "model": None, "attempts": []},
    )


def test_checkpointed_langgraph_runs_all_seven_nodes(tmp_path):
    checkpoint = tmp_path / "agent-checkpoints.sqlite"

    state = invoke_agent_graph(
        stage_definitions=_stages(),
        reasoner=_fallback_reasoner,
        configured_providers=["groq", "gemini"],
        student_id=7,
        actor_role="STUDENT",
        checkpoint_path=str(checkpoint),
        run_id="test-complete-run",
    )

    assert state["status"] == "COMPLETED"
    assert state["failed_stages"] == 0
    assert state["stages"] == [f"Agent {index}" for index in range(1, 8)]
    assert checkpoint.exists() and checkpoint.stat().st_size > 0
    for index, name in enumerate(state["stages"]):
        row = state["stage_results"][name]
        assert row["status"] == "DEGRADED"
        assert row["output"]["orchestration"] == "langgraph"
        assert row["output"]["graph_node"].startswith(f"agent_{index + 1}_")
        assert row["output"]["llm"]["provider"] == ["groq", "gemini"][index % 2]


def test_stage_failure_is_audited_without_stopping_remaining_nodes(tmp_path):
    state = invoke_agent_graph(
        stage_definitions=_stages(fail_index=2),
        reasoner=_fallback_reasoner,
        configured_providers=[],
        student_id=9,
        actor_role="STUDENT",
        checkpoint_path=str(tmp_path / "failure-checkpoints.sqlite"),
        run_id="test-partial-run",
    )

    assert state["status"] == "PARTIAL_FAILURE"
    assert state["failed_stages"] == 1
    assert len(state["stage_results"]) == 7
    assert state["stage_results"]["Agent 3"]["status"] == "FAILED"
    assert state["stage_results"]["Agent 3"]["output"]["error"] == "ValueError"
    assert all(
        state["stage_results"][f"Agent {index}"]["status"] == "DEGRADED"
        for index in (1, 2, 4, 5, 6, 7)
    )
