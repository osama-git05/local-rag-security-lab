"""Run optional real-browser payment checks against the existing local API.

Requires Node, Playwright and an installed Chrome; never installs dependencies.
"""
import argparse
import os
import subprocess

from dotenv import dotenv_values
from app.paths import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", default="node")
    parser.add_argument("--node-modules", help="Optional existing Node module directory")
    args = parser.parse_args()
    values = dotenv_values(ROOT / ".env")
    if not all(values.get(key) for key in ("ADMIN_TOKEN", "EMPLOYEE_TOKEN")):
        print("Existing local employee and administrator credentials are required.")
        return 2
    environment = os.environ.copy()
    environment["PAYMENT_UI_ADMIN_TOKEN"] = values["ADMIN_TOKEN"]
    environment["PAYMENT_UI_EMPLOYEE_TOKEN"] = values["EMPLOYEE_TOKEN"]
    if args.node_modules:
        environment["NODE_PATH"] = args.node_modules
    try:
        return subprocess.run([args.node, str(ROOT / "tests/live/check_payment_ui.cjs")],
                              cwd=ROOT, env=environment, timeout=120).returncode
    except (OSError, subprocess.TimeoutExpired):
        print("Browser checks could not finish. Check the existing Node/browser setup and API.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
