from __future__ import annotations

import os


def main() -> None:
    """Run CLI interface."""
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    try:
        from valutatrade_hub.logging_config import setup_logging

        setup_logging()
    except Exception:
        pass

    from valutatrade_hub.cli.interface import main as cli_main

    cli_main()
