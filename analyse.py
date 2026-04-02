#!/usr/bin/env python3
"""COBOL Reverse Engineering Agent -- thin entry point.

See orchestrator/ for the implementation.
"""

import asyncio

from orchestrator.cli import main

if __name__ == "__main__":
    asyncio.run(main())
