"""Allow `python -m changelog_drafter`."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
