"""Count characters in UTF-8 text from a file or stdin; optionally enforce a limit."""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, nargs="?")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    text = args.path.read_text(encoding="utf-8") if args.path else sys.stdin.read()
    text = text.rstrip("\r\n")
    print(f"{len(text)} characters")
    if args.limit is not None and len(text) > args.limit:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
