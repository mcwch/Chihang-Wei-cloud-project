from config import Config


def test_config_uses_generic_serverless_function_url():
    assert isinstance(
        Config.SERVERLESS_FUNCTION_URL,
        str,
    )
    assert not hasattr(
        Config,
        "DIGITALOCEAN_FUNCTION_URL",
    )


def test_config_has_admin_password_setting():
    assert isinstance(
        Config.ADMIN_PASSWORD,
        str,
    )
