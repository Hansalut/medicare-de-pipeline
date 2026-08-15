"""
Pipeline orchestrator: runs extract -> transform -> load as one
reproducible command. This is a manual stand-in for what a scheduler
like Airflow would automate in production (see README).
"""

import sys
import subprocess

STEPS = [
    ("Extract", "src/extract.py"),
    ("Transform", "src/transform.py"),
    ("Load", "src/load.py"),
]


def run_step(name, script_path):
    print(f"\n{'=' * 50}\nSTEP: {name}\n{'=' * 50}")
    result = subprocess.run([sys.executable, script_path])
    if result.returncode != 0:
        print(f"\nPipeline FAILED at step: {name}")
        sys.exit(1)


if __name__ == "__main__":
    for name, script in STEPS:
        run_step(name, script)
    print(f"\n{'=' * 50}\nPipeline completed successfully.\n{'=' * 50}")