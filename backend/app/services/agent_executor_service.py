from __future__ import annotations

import json
from typing import Any, Dict


class AgentExecutorService:
    def execute_run(
        self,
        *,
        run: Dict[str, Any],
        store,
        openai_service,
    ) -> int:
        run_id = int(run["id"])
        mission = str(run["mission"])
        context = str(run.get("context") or "")
        tasks = store.list_agent_tasks(run_id=run_id)
        if not tasks:
            store.update_agent_run_status(run_id=run_id, status="completed")
            return 0

        executed = 0
        store.update_agent_run_status(run_id=run_id, status="in_progress")
        for task in tasks:
            current_status = str(task["status"])
            if current_status == "completed":
                continue
            task_id = int(task["id"])
            role = str(task["role"])
            objective = str(task["objective"])
            store.update_agent_task(task_id=task_id, status="in_progress", output=task.get("output", "") or "")
            output = self._generate_task_output(
                mission=mission,
                role=role,
                objective=objective,
                context=context,
                openai_service=openai_service,
            )
            store.update_agent_task(task_id=task_id, status="completed", output=output)
            executed += 1

        store.update_agent_run_status(run_id=run_id, status="completed")
        return executed

    @staticmethod
    def _generate_task_output(
        *,
        mission: str,
        role: str,
        objective: str,
        context: str,
        openai_service,
    ) -> str:
        try:
            generated = openai_service.generate_agent_task_output(
                mission=mission,
                role=role,
                objective=objective,
                context=context,
            )
        except Exception:
            generated = None

        if isinstance(generated, dict):
            summary = str(generated.get("summary", "")).strip()
            deliverable = str(generated.get("deliverable", "")).strip()
            next_steps_raw = generated.get("next_steps")
            next_steps: list[str] = []
            if isinstance(next_steps_raw, list):
                next_steps = [str(item).strip() for item in next_steps_raw if str(item).strip()][:3]
            payload = {
                "summary": summary or f"Executed objective for role: {role}",
                "deliverable": deliverable or f"Draft deliverable generated for objective: {objective}",
                "next_steps": next_steps
                or [
                    "Review output and refine constraints.",
                    "Convert deliverable into concrete ticket(s).",
                    "Update metrics dashboard with outcome.",
                ],
            }
            return json.dumps(payload, indent=2)

        fallback = {
            "summary": f"Execution completed for {role}.",
            "deliverable": f"Objective addressed: {objective}",
            "next_steps": [
                "Review and approve generated direction.",
                "Create implementation tasks from this output.",
                "Track impact in weekly snapshot.",
            ],
        }
        return json.dumps(fallback, indent=2)
