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
