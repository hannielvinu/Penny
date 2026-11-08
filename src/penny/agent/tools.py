import json
import shlex

from penny.agent.guard import Chunk
from penny.exec.gitops import git
from penny.exec.patch import atomic_write, preview
from penny.exec.shell import execute
from penny.exec.tests_runner import detect
from penny.exec.trim import trim
from penny.repo.secrets import mask
from penny.repo.slices import Slices
from penny.safety.approvals import Approval
from penny.safety.paths import safe_path
from penny.safety.risk import Risk, classify, normalized


class Tools:
    def __init__(self, root, repo_map, policy, approver, record, run_dir, ledger, techniques):
        self.root = root
        self.map = repo_map
        self.slices = Slices(repo_map, techniques.dedupe)
        self.policy = policy
        self.approver = approver
        self.record = record
        self.run_dir = run_dir
        self.ledger = ledger
        self.techniques = techniques
        self.last_tests_passed = False
        self.step = 0
        self.timeout = 120.0

    def approve(self, kind: str, risk: Risk, content: str, automatic: bool = False) -> bool:
        request = Approval(kind, risk, mask(content)[0], self.ledger.cost)
        self.record.approvals.append(request.to_dict())
        try:
            request.decision = risk != Risk.BLOCKED and (
                automatic or self.approver.approve(request)
            )
        finally:
            self.record.approvals[-1] = request.to_dict()
        return request.decision

    def run_command(self, command, *, tests=False) -> Chunk:
        risk, reason = classify(command, self.root)
        allowed = risk == Risk.LOW and normalized(command) in [
            normalized(c) for c in self.policy.auto_approve.commands
        ]
        if not self.approve("shell", risk, f"{normalized(command)}\n{reason}", allowed):
            return Chunk(
                "user denied: shell command" if risk != Risk.BLOCKED else "BLOCKED: " + reason
            )
        result = execute(self.root, command, timeout=self.timeout)
        output, found = mask(result["output"])
        raw_dir = self.run_dir / "raw"
        raw_dir.mkdir(exist_ok=True)
        (raw_dir / f"step-{self.step}.txt").write_text(output, encoding="utf-8")
        result["output"] = trim(output) if self.techniques.trim_tool_output else output
        if tests:
            self.last_tests_passed = result["returncode"] == 0
            self.record.tests.append(result)
        return Chunk(json.dumps(result), sensitivity="confidential" if found else "public")

    def dispatch(self, action: str, args: dict) -> Chunk:
        if action in {"search", "read_symbol", "read_lines", "list_dir"}:
            if not self.policy.auto_approve.reads and not self.approve(
                "read", Risk.LOW, json.dumps(args)
            ):
                return Chunk("user denied: read")
        if action == "search":
            self.map.build()
            return Chunk(json.dumps(self.map.search(args["query"], args["max_results"])))
        if action == "read_symbol":
            if self.techniques.slice_reads:
                return Chunk(
                    self.slices.symbol(args["path"], args["symbol"], self.step), args["path"]
                )
            return Chunk(self.map.read(args["path"]), args["path"])
        if action == "read_lines":
            text = (
                self.slices.lines(args["path"], args["start"], args["end"], self.step)
                if self.techniques.slice_reads
                else self.map.read(args["path"])
            )
            return Chunk(text, args["path"])
        if action == "list_dir":
            path = safe_path(self.root, args["path"])
            names = sorted(
                p.name + ("/" if p.is_dir() else "")
                for p in path.iterdir()
                if not p.is_symlink()
                and not self.map.ignore.excluded(
                    p.relative_to(self.root).as_posix() + ("/" if p.is_dir() else "")
                )
            )
            return Chunk(json.dumps(names[:200]), args["path"])
        if action in {"apply_patch", "create_file"}:
            if action == "apply_patch" and not self.techniques.patch_edits:
                return Chunk(
                    "Patch edits disabled; use create_file for new files and read_lines for context"
                )
            target, new, diff = preview(
                self.root, args["path"], args.get("edits"), args.get("content")
            )
            if not self.approve("write", Risk.MEDIUM, diff or f"Create empty file {args['path']}"):
                return Chunk("user denied: " + action)
            # Recheck symlinks and the exact snapshot after user interaction.
            checked, checked_new, checked_diff = preview(
                self.root, args["path"], args.get("edits"), args.get("content")
            )
            if checked != target or checked_new != new or checked_diff != diff:
                raise ValueError("File changed during approval; request a fresh patch")
            atomic_write(target, new)
            self.last_tests_passed = False
            if args["path"] not in self.record.files_changed:
                self.record.files_changed.append(args["path"])
            if action == "create_file":
                self.record.created_files.append(args["path"])
            return Chunk("Applied patch:\n" + diff, args["path"])
        if action == "run_tests":
            command = self.policy.test_command or detect(self.root)
            if not command:
                return Chunk("No test command detected; configure test_command")
            target = args.get("target")
            command_args = shlex.split(command)
            if target:
                safe_path(self.root, target.split("::")[0])
                if target.startswith("-"):
                    raise ValueError("Test target cannot be an option")
                command_args.append(target)
            return self.run_command(command_args, tests=True)
        if action == "run_shell":
            self.last_tests_passed = False
            return self.run_command(args["command"])
        if action == "git":
            op = args["op"]
            if op == "push" and not self.policy.git.allow_push:
                return Chunk("user denied: git push is disabled by policy")
            command = ["git", op, *args["args"]]
            risk, reason = classify(command, self.root)
            if not self.approve("git", risk, normalized(command), risk == Risk.LOW):
                return Chunk("user denied: git " + op)
            if risk == Risk.BLOCKED:
                return Chunk("BLOCKED: " + reason)
            return Chunk(git(self.root, op, *args["args"]))
        raise ValueError("Action is handled by the agent loop")
