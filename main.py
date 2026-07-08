import argparse
import subprocess
from scrape import main as scrape_main
from index import main as index_main
from chat import main as chat_main
from cleanup import cleanup as cleanup_main


def ui_main():
    subprocess.run(["streamlit", "run", "app.py"])


def batch_main():
    scrape_main()
    index_main()


def main():
    parser = argparse.ArgumentParser(
        prog="OptiBot",
        description="OptiBot RAG Pipeline",
    )

    parser.add_argument(
        "command",
        choices=[
            "scrape",
            "index",
            "chat",
            "cleanup",
            "ui",
            "batch",
        ],
        help="Pipeline command",
    )

    args = parser.parse_args()

    commands = {
        "scrape": scrape_main,
        "index": index_main,
        "chat": chat_main,
        "cleanup": cleanup_main,
        "ui": ui_main,
        "batch": batch_main,
    }

    commands[args.command]()


if __name__ == "__main__":
    main()
