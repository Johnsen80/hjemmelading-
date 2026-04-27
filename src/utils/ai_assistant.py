"""Local deterministic advisory helper.

The app should remain fully usable offline and without remote providers.
This module keeps the existing Assistant interface, but all responses are
generated locally from explicit rules and the current analysis context.
"""

from typing import Any, Dict, List, Optional


class Assistant:
    def __init__(self, model: Optional[str] = None, db: Any | None = None):
        self.model = model or "local-analysis"
        self._db = db

    def chat(
        self, message: str, history: List[str], context: Optional[Dict] = None
    ) -> str:
        """Return a local advisory response based on explicit context rules."""
        ctx = context or {}
        msg = (message or "").strip().lower()
        checks: list[str] = []
        actions: list[str] = []

        rifle = str(ctx.get("rifle") or "").strip()
        powder = str(ctx.get("powder") or "").strip()
        charge = ctx.get("charge")
        if rifle:
            checks.append(f"Rifle: {rifle}")
        if powder:
            checks.append(f"Krutt: {powder}")
        if charge is not None:
            checks.append(f"Aktuell ladning: {charge} gr")

        calibration = ctx.get("last_calibration")
        if isinstance(calibration, dict):
            mse = calibration.get("mse")
            if isinstance(mse, (int, float)):
                if mse <= 10:
                    checks.append(f"Kalibrering ser stram ut (MSE {mse:.2f})")
                elif mse <= 25:
                    checks.append(
                        f"Kalibrering er brukbar, men bør følges opp (MSE {mse:.2f})"
                    )
                else:
                    checks.append(
                        f"Kalibrering er svak og bør bekreftes med flere skudd (MSE {mse:.2f})"
                    )
                    actions.append(
                        "Logg en ny chrono-serie før du stoler på små forskjeller i fart eller trykkmargin."
                    )

        recent = ctx.get("recent_imports_summary")
        if isinstance(recent, list) and recent:
            recent_velocities = [
                float(item.get("vel"))
                for item in recent
                if isinstance(item, dict) and isinstance(item.get("vel"), (int, float))
            ]
            if recent_velocities:
                spread = max(recent_velocities) - min(recent_velocities)
                checks.append(
                    f"Siste chrono-historikk viser omtrent {spread:.0f} fps spenn"
                )
                if spread > 35:
                    actions.append(
                        "Se på temperatur, lot og settedybde før du jager en ny node."
                    )
                else:
                    actions.append(
                        "Historikken er rolig nok til å teste små steg rundt nåværende ladning."
                    )
        else:
            actions.append(
                "Importer chrono-data for å kunne rangere forslag med bedre trygghet."
            )

        plot_summary = ctx.get("plot_summary")
        if isinstance(plot_summary, dict) and plot_summary:
            y_min = plot_summary.get("y_min")
            y_max = plot_summary.get("y_max")
            n = plot_summary.get("n")
            if isinstance(y_min, (int, float)) and isinstance(y_max, (int, float)):
                checks.append(f"Plottet dekker omtrent {y_min:.1f} til {y_max:.1f}")
            if isinstance(n, int) and n < 4:
                actions.append(
                    "Datagrunnlaget i plottet er tynt. Ikke overtolk kurveform eller optimum ennå."
                )

        if any(
            token in msg
            for token in ("trykk", "pressure", "saami", "cip", "safety", "sikker")
        ):
            actions.append(
                "Hold margin mot maks trykk konservativ og bekreft med målt fart før videre opptrapping."
            )
        if any(token in msg for token in ("kalibr", "chrono", "fart", "velocity")):
            actions.append(
                "Sammenlign modell mot målt fart i like batcher før du bruker modellen som beslutningsgrunnlag."
            )
        if any(token in msg for token in ("plot", "kurve", "graf", "slope")):
            actions.append(
                "Se etter flate områder og repeterbare punkter, ikke bare laveste enkeltskudd eller peneste kurvepunkt."
            )
        if any(
            token in msg for token in ("neste", "next", "forslag", "suggest", "test")
        ):
            actions.append(
                "Neste gode steg er vanligvis et lite testvindu rundt den beste observerte ladningen, ikke et stort hopp."
            )

        if not checks:
            checks.append(
                "Lokal rådgiver bruker målt historikk, kalibrering og plottdata når det finnes."
            )
        if not actions:
            actions.append(
                "Formuler spørsmålet rundt trykk, fart, kalibrering eller neste teststeg for mer konkret råd."
            )

        body = ["Lokal vurdering:"]
        body.extend(f"- {line}" for line in checks)
        body.append("Neste steg:")
        body.extend(f"- {line}" for line in actions[:3])
        return "\n".join(body)

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
        """Persist local advisor preferences for backward compatibility."""
        try:
            cur = db.cursor
            cur.execute(
                "CREATE TABLE IF NOT EXISTS ai_settings (id INTEGER PRIMARY KEY AUTOINCREMENT, enabled INTEGER, model TEXT, api_key TEXT, created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )
            cur.execute(
                "INSERT INTO ai_settings (enabled, model, api_key) VALUES (?, ?, ?)",
                (1 if enabled else 0, model, api_key),
            )
            db.conn.commit()
            self._db = db
            self.model = model or "local-analysis"
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
