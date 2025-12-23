"""Simple AI assistant wrapper.

This module provides a minimal `Assistant` class with a `chat(message, history)`
method. It uses a local stub response by default. If the `openai` package is
installed and the `OPENAI_API_KEY` environment variable is set, it will attempt
to call OpenAI's ChatCompletion (best-effort). The wrapper intentionally keeps
integration optional and simple so the UI remains usable offline.
"""

import os
from typing import Dict, List, Optional


class Assistant:
    def __init__(self, model: str = None, db: Optional[object] = None):
        self.model = model or os.environ.get("AI_ASSISTANT_MODEL", "gpt-4o-mini")
        self._enabled = False
        self.openai = None
        self._db = db

        # If a DB is provided, try to load settings from it
        if db is not None:
            try:
                cur = db.cursor
                cur.execute(
                    "SELECT enabled, model, api_key FROM ai_settings ORDER BY id DESC LIMIT 1"
                )
                row = cur.fetchone()
                if row:
                    enabled = bool(row[0])
                    model_val = row[1]
                    api_key = row[2]
                    if model_val:
                        self.model = model_val
                    if api_key:
                        try:
                            import openai

                            openai.api_key = api_key
                            self.openai = openai
                            self._enabled = enabled
                        except Exception:
                            self.openai = None
                            self._enabled = False
                    else:
                        self._enabled = enabled and False
            except Exception:
                # fallback to env-based init below
                pass

        # If openai not set by DB, try env
        if self.openai is None:
            try:
                import openai

                key = os.environ.get("OPENAI_API_KEY")
                if key:
                    openai.api_key = key
                    self.openai = openai
                    self._enabled = True
            except Exception:
                self.openai = None
                # keep enabled False unless DB said otherwise

    def chat(
        self, message: str, history: List[str], context: Optional[Dict] = None
    ) -> str:
        """Return assistant response. Accepts optional `context` dict with extra state.

        When a remote API is available, the context is included as system/user messages.
        When offline, the stub uses the context to tailor responses.
        """
        ctx = context or {}

        if self._enabled and self.openai:
            try:
                messages = [
                    {
                        "role": "system",
                        "content": "You are an expert reloading assistant. Answer concisely and safely.",
                    },
                ]
                # include context as system-level info
                if ctx:
                    messages.append({"role": "system", "content": f"Context: {ctx}"})
                messages.append({"role": "user", "content": message})

                resp = self.openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=512,
                )
                if resp and getattr(resp, "choices", None):
                    return resp.choices[0].message.content.strip()
            except Exception:
                pass

        # Offline stub — incorporate some context hints
        summary = []
        if ctx.get("rifle"):
            summary.append(f"Rifle={ctx.get('rifle')}")
        if ctx.get("charge") is not None:
            summary.append(f"Charge={ctx.get('charge')}gr")
        if ctx.get("last_calibration"):
            cal = ctx.get("last_calibration")
            summary.append(f"Cal(MSE)={cal.get('mse'):.2f}")
        recent = ctx.get("recent_imports_summary")
        if recent:
            summary.append(f"Recent imports={len(recent)}")

        msg = message.lower()
        if "calib" in msg or "calibrate" in msg:
            return (
                "I can help review calibrations. Use 'Show Calibration' to view predicted vs measured. "
                "If you provide chronograph imports I can suggest acceptance criteria."
            )
        if "pressure" in msg or "saami" in msg or "safety" in msg:
            return (
                "Keep predicted peak pressure ~5-10% below the SAAMI/CIP limit. "
                "Enable safety gating in the optimizer."
            )
        if "suggest" in msg or "next" in msg or "test" in msg:
            if recent:
                return "Based on recent chronograph imports I recommend testing +/-0.5gr steps around the best-performing charge, or running a 3-point ladder spaced by 0.5gr to estimate slope."
            return (
                "Try testing +/-0.5gr steps around the current charge, or run a small ladder of 3-5 charges. "
                "Provide chronograph imports to get specific suggestions."
            )
        # generic fallback with context hint
        hint = ", ".join(summary) if summary else ""
        return f"(stub) I can explain graphs and suggest safe ranges. {hint}".strip()

    def persist_chat(self, db, user_message: str, assistant_response: str) -> None:
        """Persist a chat message pair to `ai_chat_history` table (creates table if missing)."""
        try:
            cur = db.cursor
            cur.execute(
                "CREATE TABLE IF NOT EXISTS ai_chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, assistant TEXT, created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )
            cur.execute(
                "INSERT INTO ai_chat_history (user, assistant) VALUES (?, ?)",
                (user_message, assistant_response),
            )
            db.conn.commit()
        except Exception:
            # best-effort persistence; ignore failures
            pass

    def save_settings(
        self, db, enabled: bool, model: Optional[str], api_key: Optional[str]
    ) -> None:
        """Save assistant settings to `ai_settings` table."""
        try:
            cur = db.cursor
            cur.execute(
                "INSERT INTO ai_settings (enabled, model, api_key) VALUES (?, ?, ?)",
                (1 if enabled else 0, model, api_key),
            )
            db.conn.commit()
            # update local state
            self._db = db
            self.model = model or self.model
            if api_key:
                try:
                    import openai

                    openai.api_key = api_key
                    self.openai = openai
                    self._enabled = enabled
                except Exception:
                    self.openai = None
                    self._enabled = False
        except Exception:
            pass

    def fetch_recent_chats(self, db, limit: int = 20) -> List[Dict]:
        """Return recent chat history rows as dicts.

        Best-effort; returns empty list on error.
        """
        try:
            cur = db.cursor
            cur.execute(
                "SELECT id, user, assistant, created_date FROM ai_chat_history ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall() or []
            out = []
            for r in rows:
                out.append(
                    {"id": r[0], "user": r[1], "assistant": r[2], "created_date": r[3]}
                )
            return out
        except Exception:
            return []
