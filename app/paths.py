"""Stable repository paths and deliberate source discovery."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PAYMENTS_DB = ROOT / "data" / "payments.sqlite3"
SOURCE_DIRECTORIES = ("app", "scripts", "evaluation", "experiments", "tests")
def source_files():
    return sorted(path for directory in SOURCE_DIRECTORIES for path in (ROOT / directory).rglob("*.py"))


def asset_files():
    """Include the local interface in reproducibility checks."""
    directories = (ROOT / "app" / "static", ROOT / "scripts" / "console_static")
    return sorted(path for directory in directories for path in directory.rglob("*") if path.is_file())
