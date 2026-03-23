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

    class DummyCollection:
        def __init__(self):
            self.docs = {}

        def create_index(self, *_args, **_kwargs):
            return None

        def find_one(self, query):
            return self.docs.get(query.get("isin"))

        def replace_one(self, query, payload, upsert=False):
            self.docs[query.get("isin")] = payload
            return None

    class DummyDB:
        def __init__(self):
            self.collections = {}

        def __getitem__(self, name):
            if name not in self.collections:
                self.collections[name] = DummyCollection()
            return self.collections[name]

    class DummyMongoClient:
        def __init__(self, *_args, **_kwargs):
            self.dbs = {}
            self.admin = types.SimpleNamespace(command=lambda *_a, **_kw: {"ok": 1})

        def __getitem__(self, name):
            if name not in self.dbs:
                self.dbs[name] = DummyDB()
            return self.dbs[name]

    pymongo_module.MongoClient = DummyMongoClient
    errors_module.PyMongoError = DummyPyMongoError
    pymongo_module.errors = errors_module

    sys.modules["pymongo"] = pymongo_module
    sys.modules["pymongo.errors"] = errors_module
