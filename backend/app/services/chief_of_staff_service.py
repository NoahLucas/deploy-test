from __future__ import annotations

from typing import Any, Dict, List

from app.models import AgentTaskSpec


class ChiefOfStaffService:
    def build_plan(
        self,
        *,
        mission: str,
        context: str,
        requested_tasks: List[AgentTaskSpec],
        openai_service,
    ) -> Dict[str, Any]:
        if requested_tasks:
            return {
                "planner_summary": "Operator supplied explicit task list. Chief of Staff registered and prioritized execution.",
                "tasks": [
                    {
                        "role": task.role,
                        "objective": task.objective,
                        "priority": int(task.priority),
                    }
                    for task in requested_tasks
                ],
            }

        generated = None
        try:
            generated = openai_service.generate_chief_plan(mission=mission, context=context)
        except Exception:
            generated = None

        normalized = self._normalize_generated(generated)
        if normalized is not None:
            return normalized

        return {
            "planner_summary": (
                "Chief of Staff initialized a baseline distributed plan across strategy, content, systems, and metrics."
            ),
            "tasks": [
                {
                    "role": "strategy-agent",
                    "objective": "Decompose internal mission into weekly outcomes and decision gates.",
                    "priority": 3,
                },
                {
                    "role": "content-agent",
                    "objective": "Generate notes backlog and one publish-ready draft aligned to internal operating goals.",
                    "priority": 2,
                },
                {
                    "role": "systems-agent",
                    "objective": "Validate endpoint toggles and integration health across OpenAI, Apple, and Squarespace.",
                    "priority": 2,
                },
                {
                    "role": "analytics-agent",
                    "objective": "Define success metrics and produce weekly readout template with experiments.",
                    "priority": 1,
                },
            ],
        }

    @staticmethod
    def _normalize_generated(payload: Any) -> Dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        raw_tasks = payload.get("tasks")
        planner_summary = payload.get("planner_summary")
        if not isinstance(raw_tasks, list) or not isinstance(planner_summary, str):
            return None

        tasks = []
        for raw in raw_tasks:
            if not isinstance(raw, dict):
                continue
            role = raw.get("role")
            objective = raw.get("objective")
            priority = raw.get("priority", 1)
            if not isinstance(role, str) or not isinstance(objective, str):
                continue
            try:
                p = int(priority)
            except Exception:
                p = 1
            tasks.append(
                {
                    "role": role.strip()[:80],
                    "objective": objective.strip()[:2000],
                    "priority": max(0, min(3, p)),
                }
            )

        if not tasks:
            return None

        return {
            "planner_summary": planner_summary.strip()[:2000],
            "tasks": tasks[:16],
        }
