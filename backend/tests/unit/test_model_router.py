from app.services.model_router import ModelRouter


def test_routes_simple_and_dashboard_questions_to_fast_model():
    route = ModelRouter.select("¿Qué ticket llegó hoy?", ticket_context=False)
    assert route.route == "fast"
    assert route.model == "gemini-3.5-flash"


def test_routes_complex_ticket_question_to_reasoning_model():
    route = ModelRouter.select("Ya probé varias veces y sigue igual el consumo del PMIC", ticket_context=True)
    assert route.route == "reasoning"
    assert route.model == "gemini-3.6-flash"


def test_repeated_ticket_question_escalates_to_reasoning_model():
    prior = [type("Message", (), {"role": "technician", "content": "¿Cómo reviso el pin de carga?"})()]
    route = ModelRouter.select("¿Cómo reviso el pin de carga?", ticket_context=True, prior_messages=prior)
    assert route.route == "reasoning"
