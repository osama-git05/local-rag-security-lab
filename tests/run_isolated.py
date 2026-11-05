"""Run all model-free check scripts, preserving their exit status."""
import subprocess
import sys
from app.paths import ROOT

def main():
    failed = False
    for path in sorted((ROOT / "tests" / "isolated").glob("check_*.py")):
        module = ".".join(path.relative_to(ROOT).with_suffix("").parts)
        result = subprocess.run([sys.executable, "-m", module], cwd=ROOT)
        failed |= result.returncode != 0
    return int(failed)

if __name__ == "__main__":
    sys.exit(main())
