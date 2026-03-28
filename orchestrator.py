import logging
import subprocess
import sys
from pathlib import Path

from finanzuebersicht_shared import (
    ENV_FILE,
    configure_application_logging,
    docker_compose_command,
    ensure_local_env_file,
    get_settings,
)

LOG_DIR = Path(__file__).resolve().parent / "logs"
ORCHESTRATOR_LOG = LOG_DIR / "orchestrator.log"
PROJECT_ROOT = Path(__file__).resolve().parent

def _uv_executable() -> str:
    import shutil

    uv_bin = shutil.which("uv")
    if uv_bin:
        return uv_bin
    raise RuntimeError("'uv' wurde nicht im PATH gefunden. Bitte uv installieren und erneut starten.")


def _spawn_project(project: str, script: str) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [_uv_executable(), "run", "--project", project, script],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def _ensure_mongodb_started() -> bool:
    logger = logging.getLogger(__name__)
    compose_cmd = docker_compose_command()
    if not compose_cmd:
        logger.warning("Docker Compose wurde nicht gefunden. MongoDB muss manuell laufen.")
        return False

    compose_file = PROJECT_ROOT / "docker-compose.yml"
    if not compose_file.exists():
        logger.warning("Keine docker-compose.yml gefunden. MongoDB-Start wird übersprungen.")
        return False

    try:
        command = compose_cmd + ["-f", str(compose_file), "up", "-d", "mongodb"]
        logger.info("Starte MongoDB via Docker: %s", " ".join(command))
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
        return True
    except subprocess.CalledProcessError:
        logger.exception("MongoDB konnte per Docker Compose nicht gestartet werden")
        return False


def main() -> int:
    settings = get_settings()
    configure_application_logging(
        log_file=ORCHESTRATOR_LOG,
        service_name="orchestrator",
        verbosity=settings.log_verbosity,
        performance_logging=settings.performance_logging,
    )
    logger = logging.getLogger(__name__)
    logger.info("Orchestrator-Start: starte FrontendService + markedataservice")

    ensure_local_env_file()
    logger.info("Verwende env-Datei: %s", ENV_FILE)
    _ensure_mongodb_started()

    try:
        market_process = _spawn_project("markedataservice", "markedataservice")
    except RuntimeError as exc:
        logger.error("Orchestrator-Abbruch: %s", exc)
        return 2

    logger.info("Orchestrator: markedataservice gestartet (PID=%s)", market_process.pid)

    try:
        frontend_exit = _spawn_project("FrontendService", "frontendservice").wait()
        logger.info("Orchestrator: FrontendService beendet (Exit-Code=%s)", frontend_exit)
        return frontend_exit
    finally:
        if market_process.poll() is None:
            logger.info("Orchestrator: stoppe markedataservice")
            market_process.terminate()
            try:
                market_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("markedataservice reagiert nicht, erzwinge Kill")
                market_process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
