from app.schemas.auth_schema import LoginRequest


def test_login_accepts_phone_number_identifier():
    payload = LoginRequest.model_validate({
        "phone_number": "+916393645985",
        "password": "StrongPass123!",
    })

    assert payload.phone_number == "+916393645985"
    assert payload.email is None
    assert payload.password == "StrongPass123!"
