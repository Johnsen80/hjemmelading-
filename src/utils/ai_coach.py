"""Local coach for ballistics, weather, and terrain explanations.

This legacy compatibility module keeps the original function name, but the
response is now generated locally so the app remains offline-first.
"""


def get_ai_coach_response(question, lang="no"):
    """Return a short local explanation in Norwegian or English."""
    user_question = (question or "").strip()
    language = "no" if str(lang).lower().startswith("no") else "en"

    if not user_question:
        if language == "no":
            return (
                "Lokal veileder trenger et konkret spørsmål. Spør om ballistikk, vær, "
                "terreng, sikkerhetsmargin eller neste teststeg."
            )
        return (
            "Local guidance needs a concrete question. Ask about ballistics, weather, "
            "terrain, safety margin, or the next test step."
        )

    text = user_question.lower()

    if any(
        token in text
        for token in (
            "vær",
            "vind",
            "weather",
            "wind",
            "density altitude",
            "temperature",
            "temperatur",
        )
    ):
        if language == "no":
            return (
                "Lokal vurdering: Miljødata bør behandles som first-class input. "
                "Logg temperatur, trykk og vind før du tolker små forskjeller i drop eller fart. "
                "Hvis forholdene er antatt i stedet for målt, bør confidence ned og uncertainty opp."
            )
        return (
            "Local assessment: treat environmental data as first-class input. "
            "Log temperature, pressure, and wind before interpreting small changes in drop or velocity. "
            "If conditions are assumed rather than measured, confidence should go down and uncertainty should go up."
        )

    if any(
        token in text
        for token in (
            "terreng",
            "terrain",
            "leeside",
            "ridge",
            "mirage",
            "kanalvind",
            "channel wind",
        )
    ):
        if language == "no":
            return (
                "Lokal vurdering: bruk terreng som risikosignal, ikke falsk eksakt sannhet. "
                "Se spesielt etter rygg, renne, leeside, vann og store høydeforskjeller som kan gi termikk eller kanalvind."
            )
        return (
            "Local assessment: treat terrain as a risk signal, not false precision. "
            "Watch for ridges, gullies, lee-side exposure, water, and major elevation changes that can create thermals or channel wind."
        )

    if any(
        token in text
        for token in ("trykk", "pressure", "saami", "cip", "sikker", "safe", "safety")
    ):
        if language == "no":
            return (
                "Lokal vurdering: hold trykkmargin konservativ. "
                "Bruk målt fart, hylsesignaler og repeterbare serier før du trekker sterke konklusjoner om hvor nær maks du ligger."
            )
        return (
            "Local assessment: keep pressure margin conservative. "
            "Use measured velocity, case signs, and repeatable shot strings before drawing strong conclusions about how close you are to max."
        )

    if any(
        token in text
        for token in (
            "ballistikk",
            "ballistics",
            "drop",
            "drift",
            "velocity",
            "fart",
            "bc",
            "g7",
            "g1",
        )
    ):
        if language == "no":
            return (
                "Lokal vurdering: skill tydelig mellom målt, modellert, utledet og anbefalt. "
                "Bruk samme dragmodell og samme miljøgrunnlag på tvers av workflow, builder og rapporter hvis du vil ha konsistente svar."
            )
        return (
            "Local assessment: keep measured, modeled, derived, and recommended values separate. "
            "Use the same drag model and the same environmental basis across workflow, builder, and reports if you want consistent answers."
        )

    if language == "no":
        return (
            "Lokal vurdering: still spørsmålet mer konkret rundt målt data, modell, usikkerhet eller neste verifisering. "
            "Da kan veilederen gi et mer nyttig og sporbar råd."
        )
    return (
        "Local assessment: make the question more specific around measured data, model behavior, uncertainty, or the next verification step. "
        "That gives the guide a more useful and traceable answer."
    )
