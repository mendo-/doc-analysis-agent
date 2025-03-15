import os
import sys
from dotenv import load_dotenv
import pytest


def main():
    # Load environment variables from .env
    load_dotenv()

    # Run pytest with any command line arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else ["tests/integration/", "-v"]
    sys.exit(pytest.main(args))


if __name__ == "__main__":
    main()
