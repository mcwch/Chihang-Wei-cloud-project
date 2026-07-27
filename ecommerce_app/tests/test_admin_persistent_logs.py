from app import create_app


def build_admin_logging_app(tmp_path):
    log_directory = tmp_path / "logs"

    app = create_app(
        {
            "TESTING": True,
            "ADMIN_PASSWORD": "test-admin-password",
            "INSTANCE_NAME": "Admin Log Test Instance",
            "LOG_DIR": str(log_directory),
        }
    )

    return app, log_directory


def sign_in_admin(client):
    with client.session_transaction() as session:
        session["is_admin"] = True


def flush_logger(logger):
    for handler in logger.handlers:
        handler.flush()


def normalize_html(response):
    return " ".join(
        response.get_data(as_text=True).split()
    )


def test_admin_logs_page_displays_persistent_log_files(
    tmp_path,
):
    app, log_directory = build_admin_logging_app(
        tmp_path
    )

    application_logger = app.extensions[
        "application_logger"
    ]

    application_logger.info(
        "event=application_test message=application-entry"
    )
    flush_logger(application_logger)

    load_balancer_log = (
        log_directory / "load_balancer.log"
    )
    load_balancer_log.write_text(
        (
            "2026-07-26 08:00:00 WARNING "
            "event=became_unhealthy "
            "backend=Instance 2\n"
        ),
        encoding="utf-8",
    )

    client = app.test_client()
    sign_in_admin(client)

    response = client.get("/admin/logs")
    html = normalize_html(response)

    assert response.status_code == 200
    assert "Admin Logs" in html
    assert "Security Audit Log" in html
    assert "Application Log" in html
    assert "Load Balancer Log" in html
    assert "application-entry" in html
    assert "event=became_unhealthy" in html
    assert "backend=Instance 2" in html


def test_persistent_logs_show_newest_entries_first(
    tmp_path,
):
    app, log_directory = build_admin_logging_app(
        tmp_path
    )

    application_logger = app.extensions[
        "application_logger"
    ]

    application_logger.info(
        "event=application_old"
    )
    application_logger.info(
        "event=application_new"
    )
    flush_logger(application_logger)

    load_balancer_log = (
        log_directory / "load_balancer.log"
    )
    load_balancer_log.write_text(
        (
            "2026-07-26 08:00:00 INFO "
            "event=load_balancer_old\n"
            "2026-07-26 08:01:00 ERROR "
            "event=load_balancer_new\n"
        ),
        encoding="utf-8",
    )

    client = app.test_client()
    sign_in_admin(client)

    response = client.get("/admin/logs")
    html = normalize_html(response)

    assert html.index(
        "event=application_new"
    ) < html.index(
        "event=application_old"
    )

    assert html.index(
        "event=load_balancer_new"
    ) < html.index(
        "event=load_balancer_old"
    )


def test_admin_logs_page_handles_empty_or_missing_files(
    tmp_path,
):
    app, log_directory = build_admin_logging_app(
        tmp_path
    )

    load_balancer_log = (
        log_directory / "load_balancer.log"
    )

    if load_balancer_log.exists():
        load_balancer_log.unlink()

    client = app.test_client()
    sign_in_admin(client)

    response = client.get("/admin/logs")
    html = normalize_html(response)

    assert response.status_code == 200

    assert (
        "No application log entries are available."
        in html
    )

    assert (
        "No load balancer log entries are available."
        in html
    )


def test_admin_log_console_styles_are_defined():
    from pathlib import Path

    stylesheet = (
        Path(__file__).resolve().parents[1]
        / "static"
        / "style.css"
    ).read_text(encoding="utf-8-sig")

    assert ".admin-log-section" in stylesheet
    assert ".persistent-log-list" in stylesheet
    assert ".persistent-log-entry" in stylesheet

    assert "max-height: 420px" in stylesheet
    assert "overflow: auto" in stylesheet
    assert "font-family: Consolas" in stylesheet
