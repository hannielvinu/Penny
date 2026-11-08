import fnmatch
import re
from pathlib import PurePosixPath

SECRET_PATTERNS = [
    re.compile(r"AKIA[A-Z0-9]{16}"),
    re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?(?:-----END [^-]+-----|$)"
    ),
    re.compile(r"(?i)(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[^\s'\",;]{8,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
    re.compile(r"\bsk-(?:bf-)?[A-Za-z0-9_-]{16,}"),
]


def mask(text: str) -> tuple[str, bool]:
    found = False
    for pattern in SECRET_PATTERNS:
        text, count = pattern.subn("[SECRET]", text)
        found |= count > 0
    return text, found


def secret_path(path: str) -> bool:
    patterns = (".env*", "*.pem", "*.key", "id_rsa*", "*.p12", ".aws", ".ssh", ".git")
    return any(
        fnmatch.fnmatch(part.lower(), pat) for part in PurePosixPath(path).parts for pat in patterns
    )
