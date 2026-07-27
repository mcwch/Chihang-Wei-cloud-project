from logging.handlers import RotatingFileHandler

from app import create_app


def create_logging_app(tmp_path, instance_name="Logging Test Instance"):
    log_directory = tmp_path / "logs"

    app = create_app(
        {
            "TESTING": True,
            "INSTANCE_NAME": instance_name,
            "LOG_DIR": str(log_directory),
        }
    )

    return app, log_directory / "app.log"


def flush_application_logger(app):
    logger = app.extensions["application_logger"]

    for handler in logger.handlers:
        handler.flush()


def find_log_line(log_text, path):
    return next(
        line
        for line in log_text.splitlines()
        if f"path={path}" in line
    )


def test_create_app_creates_log_directory_and_file(tmp_path):
    app, log_file = create_logging_app(tmp_path)

    assert app is not None
    assert log_file.parent.is_dir()
    assert log_file.is_file()


def test_application_logger_uses_rotating_file_handler(tmp_path):
    app, _ = create_logging_app(tmp_path)

    logger = app.extensions["application_logger"]

    assert any(
        isinstance(handler, RotatingFileHandler)
        for handler in logger.handlers
    )


def test_successful_request_is_written_to_application_log(tmp_path):
    app, log_file = create_logging_app(tmp_path)
    client = app.test_client()

    response = client.get("/admin/login")
    flush_application_logger(app)

    assert response.status_code == 200

    log_text = log_file.read_text(encoding="utf-8")
    log_line = find_log_line(log_text, "/admin/login")

    assert "INFO" in log_line
    assert "instance=Logging Test Instance" in log_line
    assert "method=GET" in log_line
    assert "status=200" in log_line
    assert "response_time_ms=" in log_line


def test_missing_page_is_logged_as_warning(tmp_path):
    app, log_file = create_logging_app(tmp_path)
    client = app.test_client()

    response = client.get("/missing-logging-page")
    flush_application_logger(app)

    assert response.status_code == 404

    log_text = log_file.read_text(encoding="utf-8")
    log_line = find_log_line(
        log_text,
        "/missing-logging-page",
    )

    assert "WARNING" in log_line
    assert "method=GET" in log_line
    assert "status=404" in log_line


def test_application_log_appends_after_app_recreation(tmp_path):
    first_app, log_file = create_logging_app(
        tmp_path,
        instance_name="First Logging Instance",
    )
    first_client = first_app.test_client()

    first_client.get("/admin/login")
    flush_application_logger(first_app)

    second_app, _ = create_logging_app(
        tmp_path,
        instance_name="Second Logging Instance",
    )
    second_client = second_app.test_client()

    second_client.get("/missing-persistence-check")
    flush_application_logger(second_app)

    log_text = log_file.read_text(encoding="utf-8")

    assert "instance=First Logging Instance" in log_text
    assert "path=/admin/login" in log_text

    assert "instance=Second Logging Instance" in log_text
    assert "path=/missing-persistence-check" in log_text

    assert log_text.count(
        "path=/missing-persistence-check"
    ) == 1


def test_health_and_static_requests_are_not_logged(tmp_path):
    app, log_file = create_logging_app(tmp_path)
    client = app.test_client()

    client.get("/health")
    client.get("/static/missing-file.css")
    client.get("/admin/login")

    flush_application_logger(app)

    log_text = log_file.read_text(encoding="utf-8")

    assert "path=/admin/login" in log_text
    assert "path=/health" not in log_text
    assert "path=/static/" not in log_text


def test_unhandled_exception_logs_traceback(tmp_path):
    app, log_file = create_logging_app(tmp_path)
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.get("/force-logging-error")
    def force_logging_error():
        raise RuntimeError("forced logging failure")

    client = app.test_client()
    response = client.get("/force-logging-error")

    flush_application_logger(app)

    assert response.status_code == 500

    log_text = log_file.read_text(encoding="utf-8")

    assert "ERROR" in log_text
    assert "path=/force-logging-error" in log_text
    assert "RuntimeError: forced logging failure" in log_text
    assert "Traceback" in log_text
