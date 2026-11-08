import importlib.util
from pathlib import Path

import yaml

from penny.exec.shell import execute


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generate_sandbox", Path("benchmark/generate_sandbox.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generator_deterministic_and_suite(tmp_path):
    generator = load_generator()
    one, two = tmp_path / "one", tmp_path / "two"
    generator.generate(one)
    generator.generate(two)
    files = list(one.rglob("*.py"))
    for path in files:
        assert path.read_bytes() == (two / path.relative_to(one)).read_bytes()
    modules = [p for p in (one / "shopkit").rglob("*.py") if p.name != "__init__.py"]
    assert len(modules) == 40
    lines = sum(len(p.read_text().splitlines()) for p in modules)
    assert 3000 <= lines <= 5000
    result = execute(one, ["python", "-m", "pytest", "-q"])
    assert result["returncode"] == 0, result["output"]


def test_each_registered_task_breaks_acceptance(tmp_path):
    generator = load_generator()
    tasks = yaml.safe_load(Path("benchmark/tasks.yaml").read_text())["tasks"]
    assert len(tasks) == 8
    for task in tasks:
        root = tmp_path / task["id"]
        generator.generate(root)
        for patch in task["setup"]:
            path = root / patch["path"]
            text = path.read_text()
            assert patch["search"] in text
            text = text.replace(patch["search"], patch["replace"], -1 if patch.get("all") else 1)
            path.write_text(text)
        result = execute(root, ["python", "-m", "pytest", "-q"])
        assert result["returncode"] != 0, task["id"]
