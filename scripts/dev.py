#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Service:
    name: str
    path: str
    port: int


BACKEND_SERVICES: tuple[Service, ...] = (
    Service("api-gateway", "services/api-gateway", 8000),
    Service("masterdata-service", "services/masterdata-service", 8001),
    Service("person-service", "services/person-service", 8002),
    Service("account-service", "services/account-service", 8003),
    Service("portfolio-service", "services/portfolio-service", 8004),
    Service("marketdata-service", "services/marketdata-service", 8005),
    Service("analytics-service", "services/analytics-service", 8006),
)

SERVICE_BY_NAME = {service.name: service for service in BACKEND_SERVICES}


class ProcessGroup:
    def __init__(self) -> None:
        self._processes: list[subprocess.Popen[str]] = []

    def start(self, name: str, command: list[str], cwd: Path) -> None:
        print(f"[dev] starting {name}: {' '.join(command)} (cwd={cwd})")
        process = subprocess.Popen(command, cwd=cwd, text=True)
        self._processes.append(process)

    def wait(self) -> int:
        exit_code = 0
        try:
            for process in self._processes:
                code = process.wait()
                if code != 0:
                    exit_code = code
        except KeyboardInterrupt:
            print("\n[dev] stopping all processes...")
            self.terminate()
            exit_code = 130
        finally:
            self.terminate()
        return exit_code

    def terminate(self) -> None:
        for process in self._processes:
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
        for process in self._processes:
            if process.poll() is None:
                process.terminate()


def _uv_run(service: Service, *, reload_enabled: bool = True) -> list[str]:
    command = [
        "uv",
        "run",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(service.port),
    ]
    if reload_enabled:
        command.append("--reload")
    return command


def cmd_setup(_: argparse.Namespace) -> int:
    subprocess.run(["uv", "sync", "--all-packages", "--dev"], cwd=ROOT, check=True)
    return 0


def cmd_lint(_: argparse.Namespace) -> int:
    return subprocess.run(["uv", "run", "ruff", "check", "."], cwd=ROOT, check=False).returncode


def cmd_format(_: argparse.Namespace) -> int:
    format_result = subprocess.run(["uv", "run", "ruff", "format", "."], cwd=ROOT, check=False)
    if format_result.returncode != 0:
        return format_result.returncode
    return subprocess.run(
        ["uv", "run", "ruff", "check", ".", "--fix"], cwd=ROOT, check=False
    ).returncode


def cmd_test(_: argparse.Namespace) -> int:
    return subprocess.run(["uv", "run", "pytest"], cwd=ROOT, check=False).returncode


def cmd_dev_backend(_: argparse.Namespace) -> int:
    processes = ProcessGroup()
    for service in BACKEND_SERVICES:
        processes.start(service.name, _uv_run(service), ROOT / service.path)
    return processes.wait()


def _frontend_command() -> list[str] | None:
    frontend_dir = ROOT / "frontend-web"
    package_json = frontend_dir / "package.json"
    custom_command = os.getenv("FRONTEND_DEV_CMD")
    is_windows = os.name == "nt"

    if custom_command:
        if is_windows:
            return ["cmd", "/c", custom_command]
        return ["bash", "-lc", custom_command]

    if package_json.exists():
        if is_windows:
            return ["cmd", "/c", "npm install && npm run dev"]
        return ["bash", "-lc", "npm install && npm run dev"]

    return None


def cmd_dev_frontend(_: argparse.Namespace) -> int:
    frontend_dir = ROOT / "frontend-web"
    command = _frontend_command()
    if command is None:
        print(
            "[dev] frontend-web/package.json nicht gefunden. "
            "Lege ein Frontend an oder setze FRONTEND_DEV_CMD."
        )
        return 1
    return subprocess.run(command, cwd=frontend_dir, check=False).returncode


def cmd_dev(_: argparse.Namespace) -> int:
    processes = ProcessGroup()
    for service in BACKEND_SERVICES:
        processes.start(service.name, _uv_run(service), ROOT / service.path)

    frontend_dir = ROOT / "frontend-web"
    frontend_cmd = _frontend_command()
    if frontend_cmd is not None:
        processes.start("frontend-web", frontend_cmd, frontend_dir)
    else:
        print(
            "[dev] frontend-web übersprungen (kein package.json und kein FRONTEND_DEV_CMD gesetzt)."
        )

    return processes.wait()


def cmd_run_service(args: argparse.Namespace) -> int:
    service = SERVICE_BY_NAME[args.service]
    command = _uv_run(service, reload_enabled=not args.no_reload)
    return subprocess.run(command, cwd=ROOT / service.path, check=False).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Finanzuebersicht development tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = {
        "setup": cmd_setup,
        "lint": cmd_lint,
        "format": cmd_format,
        "test": cmd_test,
        "dev": cmd_dev,
        "dev-backend": cmd_dev_backend,
        "dev-frontend": cmd_dev_frontend,
    }

    for name, handler in commands.items():
        cmd_parser = subparsers.add_parser(name)
        cmd_parser.set_defaults(handler=handler)

    run_service = subparsers.add_parser("run-service", help="Start a single backend service")
    run_service.add_argument("service", choices=sorted(SERVICE_BY_NAME.keys()))
    run_service.add_argument("--no-reload", action="store_true", help="Disable uvicorn reload")
    run_service.set_defaults(handler=cmd_run_service)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
