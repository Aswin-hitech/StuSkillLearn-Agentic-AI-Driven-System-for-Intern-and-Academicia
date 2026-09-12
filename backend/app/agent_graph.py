"""LangGraph orchestration for StuSkillLink's six audited agent stages."""
from __future__ import annotations

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
from time import perf_counter
from typing import Any, TypedDict
from uuid import uuid4


StageHandler = Callable[[], dict[str, Any]]
Reasoner = Callable[[str, str, dict[str, Any], str | None], tuple[str, dict[str, Any]]]
StageDefinition = tuple[str, str, StageHandler]


class AgentState(TypedDict, total=False):
    run_id: str
    student_id: int | None
    actor_role: str
    stages: list[str]
    stage_results: dict[str, dict[str, Any]]
    failed_stages: int
    status: str
    fatal_error: str | None


def langgraph_available() -> bool:
    try:
        import langgraph  # noqa: F401
        from langgraph.checkpoint.sqlite import SqliteSaver  # noqa: F401
        return True
    except ImportError:
        return False


def _node_name(index: int, agent_name: str) -> str:
    stem = "".join(character.lower() if character.isalnum() else "_" for character in agent_name)
    return f"agent_{index + 1}_{'_'.join(part for part in stem.split('_') if part)}"


def build_graph(
    *,
    stage_definitions: Sequence[StageDefinition],
    reasoner: Reasoner,
    configured_providers: Sequence[str],
    checkpointer: Any = None,
):
    """Compile the real six-stage graph around existing deterministic services."""
    from langgraph.graph import END, START, StateGraph

    graph = StateGraph(AgentState)
    node_names: list[str] = []

    for index, (agent_name, responsibility, handler) in enumerate(stage_definitions):
        node_name = _node_name(index, agent_name)
        node_names.append(node_name)

        def stage_node(
            state: AgentState,
            *,
            name: str = agent_name,
            description: str = responsibility,
            facts_handler: StageHandler = handler,
            graph_node: str = node_name,
        ) -> dict[str, Any]:
            started = perf_counter()
            results = dict(state.get("stage_results") or {})
            failed = int(state.get("failed_stages") or 0)
            try:
                facts = facts_handler()
                results[name] = {
                    "name": name,
                    "responsibility": description,
                    "graph_node": graph_node,
                    "status": "PENDING",
                    "facts": facts,
                    "started": started,
                }
            except Exception as exc:
                failed += 1
                results[name] = {
                    "name": name,
                    "responsibility": description,
                    "graph_node": graph_node,
                    "status": "FAILED",
                    "output": {
                        "error": type(exc).__name__,
                        "reasoning": "This stage failed before producing a trusted result.",
                        "duration_ms": round((perf_counter() - started) * 1000),
                        "orchestration": "langgraph",
                        "graph_node": graph_node,
                    },
                }
            return {
                "stages": [*(state.get("stages") or []), name],
                "stage_results": results,
                "failed_stages": failed,
                "status": "RUNNING",
            }

        graph.add_node(node_name, stage_node)

    def reasoning_fanout(state: AgentState) -> dict[str, Any]:
        results = {name: dict(row) for name, row in (state.get("stage_results") or {}).items()}
        pending = [results[name] for name in state.get("stages", []) if results[name]["status"] == "PENDING"]
        failed = int(state.get("failed_stages") or 0)

        with ThreadPoolExecutor(max_workers=max(1, len(pending))) as pool:
            future_rows = {
                pool.submit(
                    reasoner,
                    row["name"],
                    row["responsibility"],
                    row["facts"],
                    configured_providers[index % len(configured_providers)] if configured_providers else None,
                ): row
                for index, row in enumerate(pending)
            }
            for future in as_completed(future_rows):
                row = future_rows[future]
                try:
                    reasoning, llm = future.result()
                    row["status"] = "COMPLETED" if llm["mode"] == "LIVE" else "DEGRADED"
                    row["output"] = {"facts": row["facts"], "reasoning": reasoning, "llm": llm}
                except Exception as exc:
                    failed += 1
                    row["status"] = "FAILED"
                    row["output"] = {
                        "facts": row["facts"],
                        "error": type(exc).__name__,
                        "reasoning": "The reasoning provider failed before producing a trusted result.",
                    }
                row["output"].update({
                    "duration_ms": round((perf_counter() - row["started"]) * 1000),
                    "orchestration": "langgraph",
                    "graph_node": row["graph_node"],
                })
                row.pop("started", None)

        return {"stage_results": results, "failed_stages": failed, "status": "REASONED"}

    def finalize(state: AgentState) -> dict[str, Any]:
        return {"status": "PARTIAL_FAILURE" if state.get("failed_stages") else "COMPLETED"}

    graph.add_node("reasoning_fanout", reasoning_fanout)
    graph.add_node("finalize", finalize)
    graph.add_edge(START, node_names[0])

    # Conditional edges preserve a clean emergency route if a future node marks
    # state as fatal, while ordinary stage failures remain isolated and audited.
    for index, node_name in enumerate(node_names):
        next_node = node_names[index + 1] if index + 1 < len(node_names) else "reasoning_fanout"

        def route_after_stage(state: AgentState, *, normal_destination: str = next_node) -> str:
            return "finalize" if state.get("fatal_error") else normal_destination

        graph.add_conditional_edges(
            node_name,
            route_after_stage,
            {next_node: next_node, "finalize": "finalize"},
        )

    graph.add_edge("reasoning_fanout", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile(checkpointer=checkpointer)


def invoke_agent_graph(
    *,
    stage_definitions: Sequence[StageDefinition],
    reasoner: Reasoner,
    configured_providers: Sequence[str],
    student_id: int | None,
    actor_role: str,
    checkpoint_path: str,
    run_id: str | None = None,
) -> AgentState:
    """Invoke a checkpointed LangGraph run and return its final serializable state."""
    from langgraph.checkpoint.sqlite import SqliteSaver

    graph_run_id = run_id or uuid4().hex
    path = Path(checkpoint_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")

    initial: AgentState = {
        "run_id": graph_run_id,
        "student_id": student_id,
        "actor_role": actor_role,
        "stages": [],
        "stage_results": {},
        "failed_stages": 0,
        "status": "STARTED",
        "fatal_error": None,
    }
    config = {"configurable": {"thread_id": graph_run_id}}
    with SqliteSaver.from_conn_string(str(path)) as checkpointer:
        graph = build_graph(
            stage_definitions=stage_definitions,
            reasoner=reasoner,
            configured_providers=configured_providers,
            checkpointer=checkpointer,
        )
        return graph.invoke(initial, config=config)
