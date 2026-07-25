import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_application_logging(app):
    configured_directory = app.config.get("LOG_DIR")

    if configured_directory:
        log_directory = Path(configured_directory)
    else:
        log_directory = Path(app.root_path) / "logs"

    log_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = log_directory / "app.log"

    handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(logging.INFO)

    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    logger = logging.Logger(
        f"novagear.application.{id(app)}",
        level=logging.INFO,
    )
    logger.propagate = False
    logger.addHandler(handler)

    app.extensions["application_logger"] = logger
    app.extensions["application_log_file"] = log_file

    return logger

def configure_load_balancer_logging(app, log_dir=None):
    configured_directory = (
        log_dir
        if log_dir is not None
        else app.config.get("LOG_DIR")
    )

    if configured_directory:
        log_directory = Path(configured_directory)
    else:
        log_directory = Path(app.root_path) / "logs"

    log_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = log_directory / "load_balancer.log"

    handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(logging.INFO)

    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    logger = logging.Logger(
        f"novagear.load_balancer.{id(app)}",
        level=logging.INFO,
    )
    logger.propagate = False
    logger.addHandler(handler)

    app.extensions["load_balancer_logger"] = logger
    app.extensions["load_balancer_log_file"] = log_file

    return logger

