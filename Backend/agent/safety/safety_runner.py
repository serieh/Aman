# safety/safety_runner.py
"""Agent-level safety wrapper — input scanning + output validation."""
from agent.safety.crisis_detector import detect_crisis
from agent.safety.grey_area_detector import detect_grey_area, format_category_hints
from agent.safety.response_validator import validate_response


def run_input_safety(user_text: str) -> dict:
    """Crisis + grey-area detection on user input."""
    crisis = detect_crisis(user_text)
    grey = detect_grey_area(user_text)

    # Determine safety tier for prompt injection
    if crisis["crisis_flag"]:
        safety_tier = "RED"
    elif grey["grey_area_flag"]:
        safety_tier = "GRAY"
    else:
        safety_tier = None

    return {
        **crisis,
        **grey,
        "safety_tier": safety_tier,
        "category_hints": format_category_hints(grey.get("grey_area_categories", [])),
    }


def run_output_safety(
    response_text: str,
    crisis_flag: bool = False,
    grey_area_flag: bool = False,
) -> dict:
    """Validate generated response before sending to user."""
    return validate_response(
        response_text,
        crisis_flag=crisis_flag,
        grey_area_flag=grey_area_flag,
    )
