"""Allow running the package as a module: python -m double_stub."""

import sys

from .cli import main

sys.exit(main())
