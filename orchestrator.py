import logging
import subprocess
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"
ORCHESTRATOR_LOG = LOG_DIR / "orchestrator.log"
PROJECT_ROOT = Path(__file__).resolve().parent
REQUIRED_FRONTEND_FILES = [
    PROJECT_ROOT / "FrontendService" / "personen.json",
    PROJECT_ROOT / "FrontendService" / "src" / "data" / "banken.json",
    PROJECT_ROOT / "FrontendService" / "src" / "data" / "kontotypen.json",
]


def configure_logging(level: int = logging.INFO) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(ORCHESTRATOR_LOG, encoding="utf-8"),
        ],
        force=True,
    )


def _validate_runtime_environment() -> bool:
    logger = logging.getLogger(__name__)
    missing = [str(path.relative_to(PROJECT_ROOT)) for path in REQUIRED_FRONTEND_FILES if not path.exists()]
    if missing:
        logger.error(
            "Orchestrator-Abbruch: erforderliche Frontend-Konfigurationsdateien fehlen: %s",
            ", ".join(missing),
        )
        return False
    return True


def _spawn(module_name: str) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-m", module_name],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def main() -> int:
    configure_logging(logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.info("Orchestrator-Start: starte FrontendService + markedataservice")

    if not _validate_runtime_environment():
        return 2

    market_process = _spawn("markedataservice.src.main")
    logger.info("Orchestrator: markedataservice gestartet (PID=%s)", market_process.pid)

    try:
        frontend_exit = _spawn("FrontendService.src.main").wait()
        logger.info("Orchestrator: FrontendService beendet (Exit-Code=%s)", frontend_exit)
        return frontend_exit
    finally:
        if market_process.poll() is None:
            logger.info("Orchestrator: stoppe markedataservice")
            market_process.terminate()
            market_process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
