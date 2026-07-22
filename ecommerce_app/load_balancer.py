import json
import threading
from copy import deepcopy
from pathlib import Path


class TargetRegistry:
    def __init__(self, config_path):
        self.config_path = Path(config_path)
        self._lock = threading.Lock()
        self._targets = []
        self._config_error = None
        self.reload()

    @property
    def config_error(self):
        with self._lock:
            return self._config_error

    def snapshot(self):
        with self._lock:
            return deepcopy(self._targets)

    def reload(self):
        try:
            payload = json.loads(
                self.config_path.read_text(
                    encoding="utf-8-sig",
                )
            )
            targets = self._validate(payload)
        except (OSError, ValueError, TypeError) as error:
            with self._lock:
                self._config_error = str(error)
                return deepcopy(self._targets)

        with self._lock:
            self._targets = targets
            self._config_error = None
            return deepcopy(self._targets)

    @staticmethod
    def _validate(payload):
        if not isinstance(payload, dict):
            raise ValueError(
                "Target configuration must be a JSON object."
            )

        targets = payload.get("targets")

        if not isinstance(targets, list):
            raise ValueError(
                "'targets' must be a JSON list."
            )

        validated = []
        names = set()
        urls = set()

        for item in targets:
            if not isinstance(item, dict):
                raise ValueError(
                    "Every target must be a JSON object."
                )

            name = item.get("name")
            url = item.get("url")

            if not isinstance(name, str) or not name.strip():
                raise ValueError(
                    "Every target requires a non-empty name."
                )

            if (
                not isinstance(url, str)
                or not url.startswith(
                    ("http://", "https://")
                )
            ):
                raise ValueError(
                    "Every target requires an HTTP or HTTPS URL."
                )

            name = name.strip()
            url = url.rstrip("/")

            if name in names:
                raise ValueError(
                    f"Duplicate target name: {name}"
                )

            if url in urls:
                raise ValueError(
                    f"Duplicate target URL: {url}"
                )

            names.add(name)
            urls.add(url)

            validated.append(
                {
                    "name": name,
                    "url": url,
                }
            )

        return validated
