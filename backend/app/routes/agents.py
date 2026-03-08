from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from app.models import (
    AgentRunDetailResponse,
    AgentRunExecuteResponse,
    AgentRunItem,
    AgentRunsResponse,
    AgentTaskItem,
    AgentTaskUpdateRequest,
    ChiefDispatchRequest,
    ChiefDispatchResponse,
)
from app.routes.deps import require_admin

router = APIRouter()


def _to_task_item(row: dict) -> AgentTaskItem:
    return AgentTaskItem(
        id=row["id"],
        run_id=row["run_id"],
        role=row["role"],
        objective=row["objective"],
        status=row["status"],
        priority=row["priority"],
        output=row.get("output") or None,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


@router.post("/agents/chief/dispatch", response_model=ChiefDispatchResponse)
def dispatch_chief(payload: ChiefDispatchRequest, request: Request) -> ChiefDispatchResponse:
    require_admin(request)

    plan = request.app.state.chief_service.build_plan(
        mission=payload.mission,
        context=payload.context,
        requested_tasks=payload.tasks,
        openai_service=request.app.state.openai_service,
    )

    store = request.app.state.store
    run_status = "queued" if payload.auto_execute else "awaiting_approval"
    run_id = store.create_agent_run(
        mission=payload.mission,
        context=payload.context,
        status=run_status,
        planner_summary=plan["planner_summary"],
    )

    created_task_ids: list[int] = []
    for task in plan["tasks"]:
        task_id = store.add_agent_task(
            run_id=run_id,
            role=task["role"],
            objective=task["objective"],
            status="queued" if payload.auto_execute else "draft",
            priority=int(task["priority"]),
        )
        created_task_ids.append(task_id)

    task_items: list[AgentTaskItem] = []
    rows = store.list_agent_tasks(run_id=run_id)
    for row in rows:
        if row["id"] in created_task_ids:
            task_items.append(_to_task_item(row))

    if payload.auto_execute:
        run = store.get_agent_run(run_id)
        if run:
            request.app.state.agent_executor_service.execute_run(
                run=run,
                store=store,
                openai_service=request.app.state.openai_service,
            )
            refreshed = store.list_agent_tasks(run_id=run_id)
            task_items = [_to_task_item(row) for row in refreshed]
            run_status = "completed"

    return ChiefDispatchResponse(
        run_id=run_id,
        mission=payload.mission,
        status=run_status,
        planner_summary=plan["planner_summary"],
        tasks=task_items,
        created_at=datetime.now(timezone.utc),
    )


@router.get("/agents/runs", response_model=AgentRunsResponse)
def list_agent_runs(request: Request) -> AgentRunsResponse:
    require_admin(request)
    rows = request.app.state.store.list_agent_runs(limit=80)
    return AgentRunsResponse(
        items=[
            AgentRunItem(
                id=row["id"],
                mission=row["mission"],
                status=row["status"],
                planner_summary=row["planner_summary"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]
    )


@router.get("/agents/runs/{run_id}", response_model=AgentRunDetailResponse)
def get_agent_run(run_id: int, request: Request) -> AgentRunDetailResponse:
    require_admin(request)
    run = request.app.state.store.get_agent_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found.")

    tasks = request.app.state.store.list_agent_tasks(run_id=run_id)
    return AgentRunDetailResponse(
        run=AgentRunItem(
            id=run["id"],
            mission=run["mission"],
            status=run["status"],
            planner_summary=run["planner_summary"],
            created_at=datetime.fromisoformat(run["created_at"]),
            updated_at=datetime.fromisoformat(run["updated_at"]),
        ),
        tasks=[_to_task_item(row) for row in tasks],
    )


@router.post("/agents/tasks/{task_id}", response_model=AgentTaskItem)
def update_agent_task(task_id: int, payload: AgentTaskUpdateRequest, request: Request) -> AgentTaskItem:
    require_admin(request)
    store = request.app.state.store

    # Resolve run id by scanning recent runs; lightweight for early foundation stage.
    runs = store.list_agent_runs(limit=200)
    for run in runs:
        tasks = store.list_agent_tasks(run_id=run["id"])
        for task in tasks:
            if task["id"] == task_id:
                store.update_agent_task(task_id=task_id, status=payload.status, output=payload.output)
                if payload.status == "completed":
                    remaining = [t for t in tasks if t["id"] != task_id and t["status"] != "completed"]
                    if not remaining:
                        store.update_agent_run_status(run_id=run["id"], status="completed")
                updated_rows = store.list_agent_tasks(run_id=run["id"])
                updated = next((row for row in updated_rows if row["id"] == task_id), None)
                if updated is None:
                    break
                return _to_task_item(updated)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent task not found.")


@router.post("/agents/runs/{run_id}/execute", response_model=AgentRunExecuteResponse)
def execute_agent_run(run_id: int, request: Request) -> AgentRunExecuteResponse:
    require_admin(request)
    store = request.app.state.store
    run = store.get_agent_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found.")

    executed = request.app.state.agent_executor_service.execute_run(
        run=run,
        store=store,
        openai_service=request.app.state.openai_service,
    )
    refreshed_run = store.get_agent_run(run_id)
    tasks = store.list_agent_tasks(run_id=run_id)
    if refreshed_run is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Run disappeared after execute.")

    return AgentRunExecuteResponse(
        run=AgentRunItem(
            id=refreshed_run["id"],
            mission=refreshed_run["mission"],
            status=refreshed_run["status"],
            planner_summary=refreshed_run["planner_summary"],
            created_at=datetime.fromisoformat(refreshed_run["created_at"]),
            updated_at=datetime.fromisoformat(refreshed_run["updated_at"]),
        ),
        tasks=[_to_task_item(row) for row in tasks],
        executed_tasks=executed,
        mode="server-sync",
    )
