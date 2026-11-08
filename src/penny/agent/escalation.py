from dataclasses import dataclass


@dataclass
class Escalation:
    tier: str = "cheap"
    patch_failures: int = 0
    json_failures: int = 0
    patch_attempts: int = 0
    test_failures: int = 0

    def reason(self) -> str | None:
        if self.patch_failures >= 2:
            return "two patch application failures"
        if self.json_failures >= 2:
            return "two JSON repair failures"
        if self.test_failures and self.patch_attempts >= 2:
            return "tests still fail after two patch attempts"
        return None
