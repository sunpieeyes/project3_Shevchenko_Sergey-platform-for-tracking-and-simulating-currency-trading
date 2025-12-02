import sys
from valutatrade_hub.cli.interface import cli_entrypoint

def main(argv: list[str] | None = None) -> None:
    # если аргументы не переданы — берём из командной строки
    cli_entrypoint(argv or sys.argv[1:])

if __name__ == "__main__":
    main()
