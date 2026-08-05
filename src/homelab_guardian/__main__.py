"""Allow Homelab Guardian to run with python -m homelab_guardian."""

from homelab_guardian.main import main


if __name__ == "__main__":
    raise SystemExit(main())