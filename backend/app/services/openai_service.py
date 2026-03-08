from __future__ import annotations

import json
from typing import Any, Dict, Optional

import httpx

from app.core.config import Settings


class OpenAIService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = httpx.Client(
            base_url="https://api.openai.com",
            timeout=httpx.Timeout(20.0, connect=8.0),
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
        )
        self._active_api_key = settings.openai_api_key
        self._active_model = settings.openai_model

    @property
    def active_model(self) -> str:
        return self._active_model

    def configure_runtime(self, *, api_key: str, model: Optional[str] = None) -> None:
        key = api_key.strip()
        if len(key) < 20:
            raise RuntimeError("OpenAI API key appears invalid.")
        self._active_api_key = key
        if model and model.strip():
            self._active_model = model.strip()
        self._client.headers["Authorization"] = f"Bearer {self._active_api_key}"

    def test_connectivity(self) -> Dict[str, Any]:
        self._require_key()
        payload = {
            "model": self._active_model,
            "store": False,
            "input": [{"role": "user", "content": [{"type": "text", "text": "health check"}]}],
            "max_output_tokens": 8,
        }
        response = self._client.post("/v1/responses", json=payload)
        response.raise_for_status()
        data = response.json()
        response_id = str(data.get("id", ""))
        hint = response_id[-8:] if response_id else "unknown"
        return {"model": self._active_model, "account_hint": hint}

    def create_realtime_session(
        self,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._require_key()

        payload: Dict[str, Any] = {
            "model": model or self.settings.openai_realtime_model,
            "voice": voice or self.settings.openai_realtime_voice,
        }
        if instructions:
            payload["instructions"] = instructions

        response = self._client.post("/v1/realtime/sessions", json=payload)
        response.raise_for_status()
        return response.json()

    def generate_public_brief(
        self,
        signal_averages: Dict[str, float],
        scores: Dict[str, int],
    ) -> Optional[Dict[str, str]]:
        if not self.settings.openai_api_key:
            return None

        prompt = {
            "signal_averages": signal_averages,
            "scores": scores,
        }

        payload = {
            "model": self._active_model,
            "store": False,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "You generate concise executive operating intelligence for a public website. "
                                "Never reveal raw health metrics. Output strict JSON with keys headline and action. "
                                "Headline max 28 words. Action max 16 words."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(prompt),
                        }
                    ],
                },
            ],
        }

        response = self._client.post("/v1/responses", json=payload)
        response.raise_for_status()

        payload = response.json()
        text = self._extract_text(payload)
        if not text:
            return None

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None

        headline = parsed.get("headline")
        action = parsed.get("action")
        if not isinstance(headline, str) or not isinstance(action, str):
            return None

        return {
            "headline": headline.strip(),
            "action": action.strip(),
        }

    def generate_notes_ideas(
        self,
        *,
        context: str,
        count: int,
        memory: Optional[list[Dict[str, str]]] = None,
    ) -> Optional[Dict[str, Any]]:
        self._require_key()

        prompt = {
            "context": context,
            "count": count,
            "memory": memory or [],
        }
        payload = {
            "model": self._active_model,
            "store": False,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Generate high-quality notes ideas for an operator-focused personal brand. "
                                "Return strict JSON: {\"ideas\":[{\"title\",\"thesis\",\"why_now\",\"format\",\"outline\"}]}. "
                                "outline must be exactly 5 concise bullets. "
                                "format must be one of: essay, teardown, field-note, playbook."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": json.dumps(prompt)}],
                },
            ],
        }

        response = self._client.post("/v1/responses", json=payload)
        response.raise_for_status()
        text = self._extract_text(response.json())
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict) or not isinstance(parsed.get("ideas"), list):
            return None
        return parsed

    def generate_note_draft(
        self,
        *,
        brief: str,
        target_words: int,
        memory: Optional[list[Dict[str, str]]] = None,
    ) -> Optional[Dict[str, Any]]:
        self._require_key()

        prompt = {
            "brief": brief,
            "target_words": target_words,
            "memory": memory or [],
        }
        payload = {
            "model": self._active_model,
            "store": False,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Write a publish-ready markdown note in an operator voice. "
                                "Return strict JSON with keys: "
                                "title, slug, summary, body_markdown, meta_title, meta_description, social_quotes. "
                                "social_quotes must be an array of exactly 3 strings. "
                                "slug should be lowercase-hyphen URL-safe."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": json.dumps(prompt)}],
                },
            ],
        }

        response = self._client.post("/v1/responses", json=payload)
        response.raise_for_status()
        text = self._extract_text(response.json())
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None
        return parsed

    def generate_lab_daily_brief(
        self,
        *,
        priorities: list[str],
        risks: list[str],
        context: str,
        memory: Optional[list[Dict[str, str]]] = None,
    ) -> Optional[Dict[str, Any]]:
        self._require_key()
        prompt = {
            "priorities": priorities,
            "risks": risks,
            "context": context,
            "memory": memory or [],
        }
        payload = {
            "model": self.settings.openai_model,
            "store": False,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "You generate a concise daily operating brief for an executive product leader. "
                                "Return strict JSON with keys: headline, top_actions, watchouts, communication_draft. "
                                "top_actions must contain exactly 3 strings. watchouts must contain exactly 3 strings. "
                                "communication_draft should be a short message suitable for posting to a leadership channel."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": json.dumps(prompt)}],
                },
            ],
        }

        response = self._client.post("/v1/responses", json=payload)
        response.raise_for_status()
        text = self._extract_text(response.json())
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None
        return parsed

    def generate_chief_plan(
        self,
        *,
        mission: str,
        context: str,
    ) -> Optional[Dict[str, Any]]:
        self._require_key()
        payload = {
            "model": self._active_model,
            "store": False,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "You are a chief-of-staff orchestrator for an AI-native product operation. "
                                "Return strict JSON with keys planner_summary and tasks. "
                                "tasks must be an array of objects: role, objective, priority (0-3). "
                                "Create 3-8 tasks with practical sequencing."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"mission": mission, "context": context}),
                        }
                    ],
                },
            ],
        }
        response = self._client.post("/v1/responses", json=payload)
        response.raise_for_status()
        text = self._extract_text(response.json())
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None
        return parsed

    def generate_agent_task_output(
        self,
        *,
        mission: str,
        role: str,
        objective: str,
        context: str,
    ) -> Optional[Dict[str, Any]]:
        self._require_key()
        payload = {
            "model": self._active_model,
            "store": False,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "You are an execution agent in an AI-native product operating system. "
                                "Return strict JSON with keys: summary, deliverable, next_steps. "
                                "next_steps must be an array of exactly 3 concise strings."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "mission": mission,
                                    "role": role,
                                    "objective": objective,
                                    "context": context,
                                }
                            ),
                        }
                    ],
                },
            ],
        }
        response = self._client.post("/v1/responses", json=payload)
        response.raise_for_status()
        text = self._extract_text(response.json())
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None
        return parsed

    @staticmethod
    def _extract_text(payload: Dict[str, Any]) -> str:
        output_text = payload.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        output = payload.get("output")
        if not isinstance(output, list):
            return ""

        for item in output:
            if not isinstance(item, dict):
                continue
            contents = item.get("content", [])
            if not isinstance(contents, list):
                continue
            for content in contents:
                if not isinstance(content, dict):
                    continue
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    return text.strip()
        return ""

    def _require_key(self) -> None:
        if not self._active_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
