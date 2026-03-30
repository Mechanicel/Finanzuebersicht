# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

import finanzuebersicht_shared.config as shared_config
from finanzuebersicht_shared.config import ServiceSettings


def _write_env(path: Path, *, app_name: str) -> None:
    path.write_text(f"APP_NAME={app_name}\n", encoding="utf-8")


def test_loads_root_env_when_started_from_service_dir(tmp_path, monkeypatch) -> None:
    root_dir = tmp_path / "repo"
    root_dir.mkdir()
    _write_env(root_dir / ".env", app_name="root-app")

    service_dir = root_dir / "services" / "person-service"
    service_dir.mkdir(parents=True)

    monkeypatch.chdir(service_dir)
    monkeypatch.setattr(shared_config, "_repo_root_from_config_file", lambda: root_dir)

    settings = ServiceSettings()

    assert settings.app_name == "root-app"


def test_service_env_has_priority_over_root_env(tmp_path, monkeypatch) -> None:
    root_dir = tmp_path / "repo"
    root_dir.mkdir()
    _write_env(root_dir / ".env", app_name="root-app")

    service_dir = root_dir / "services" / "person-service"
    service_dir.mkdir(parents=True)
    _write_env(service_dir / ".env", app_name="service-app")

    monkeypatch.chdir(service_dir)
    monkeypatch.setattr(shared_config, "_repo_root_from_config_file", lambda: root_dir)

    settings = ServiceSettings()

    assert settings.app_name == "service-app"


def test_process_env_has_priority_over_dotenv_files(tmp_path, monkeypatch) -> None:
    root_dir = tmp_path / "repo"
    root_dir.mkdir()
    _write_env(root_dir / ".env", app_name="root-app")

    service_dir = root_dir / "services" / "person-service"
    service_dir.mkdir(parents=True)
    _write_env(service_dir / ".env", app_name="service-app")

    monkeypatch.chdir(service_dir)
    monkeypatch.setattr(shared_config, "_repo_root_from_config_file", lambda: root_dir)
    monkeypatch.setenv("APP_NAME", "process-env-app")

    settings = ServiceSettings()

    assert settings.app_name == "process-env-app"
