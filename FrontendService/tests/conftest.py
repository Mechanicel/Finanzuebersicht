import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SHARED_ROOT = ROOT.parent / "shared_config_pkg" / "src"
if str(SHARED_ROOT) not in sys.path:
    sys.path.insert(0, str(SHARED_ROOT))

if "pymongo" not in sys.modules:
    pymongo_module = types.ModuleType("pymongo")
    errors_module = types.ModuleType("pymongo.errors")

    class DummyPyMongoError(Exception):
        pass

    class DummyMongoClient:
        def __init__(self, *args, **kwargs):
            pass

    pymongo_module.MongoClient = DummyMongoClient
    errors_module.PyMongoError = DummyPyMongoError
    pymongo_module.errors = errors_module

    sys.modules["pymongo"] = pymongo_module
    sys.modules["pymongo.errors"] = errors_module
