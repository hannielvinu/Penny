"""Build the static hosted demo. This does not deploy the Python CLI or a gateway."""

import argparse
import shutil
from pathlib import Path

from penny.report.html import receipt
from penny.report.model import RunRecord


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".penny/website-dist"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    target = args.output.resolve()
    target.mkdir(parents=True, exist_ok=True)
    for path in (root / "web").iterdir():
        if path.is_file():
            shutil.copyfile(path, target / path.name)
    shutil.copytree(root / "src/penny/report/assets/fonts", target / "fonts", dirs_exist_ok=True)
    record = RunRecord.model_validate_json((root / "web/demo.json").read_text(encoding="utf-8"))
    (target / "receipt.html").write_text(receipt(record), encoding="utf-8")
    print(f"Built static demo: {target}")


if __name__ == "__main__":
    main()
