"""Main entrypoint."""
from mulletwebhook import create_app


def main() -> None:
    """Run the mulletwebhook web server."""
    app = create_app()
    app.run(host="0.0.0.0")


if __name__ == "__main__":
    main()
