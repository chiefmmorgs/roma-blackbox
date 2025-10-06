"""Policy configuration for black-box monitoring"""

from typing import List
from dataclasses import dataclass, field


@dataclass
class Policy:
    """Privacy and security policy for black-box monitoring"""

    black_box: bool = True
    break_glass_request_ids: List[str] = field(default_factory=list)
    pii_fields: List[str] = field(
        default_factory=lambda: ["email", "wallet", "ip", "ssn", "phone", "address"]
    )
    keep_hashes: bool = True
    max_cost_cents: float = 100.0
    request_timeout_seconds: int = 300
    max_recursion_depth: int = 10
    include_code_sha: bool = True
    include_policy_hash: bool = True
    sign_attestations: bool = False
    signing_key_path: str = ""

    def __post_init__(self):
        if self.max_cost_cents <= 0:
            raise ValueError("max_cost_cents must be positive")
        if self.request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be positive")
        if self.sign_attestations and not self.signing_key_path:
            raise ValueError("signing_key_path required when sign_attestations=True")

    @classmethod
    def from_dict(cls, config: dict) -> "Policy":
        return cls(**config)

    def to_dict(self) -> dict:
        return {
            "black_box": self.black_box,
            "break_glass_request_ids": self.break_glass_request_ids,
            "pii_fields": self.pii_fields,
            "keep_hashes": self.keep_hashes,
            "max_cost_cents": self.max_cost_cents,
        }


STRICT_PRIVACY = Policy(
    black_box=True,
    break_glass_request_ids=[],
    pii_fields=["email", "wallet", "ip", "ssn", "phone", "address", "credit_card"],
    keep_hashes=True,
    max_cost_cents=50.0,
)

DEVELOPMENT = Policy(
    black_box=False,
    break_glass_request_ids=["*"],
    pii_fields=[],
    keep_hashes=False,
    max_cost_cents=1000.0,
)

PRODUCTION = Policy(
    black_box=True,
    break_glass_request_ids=[],
    pii_fields=["email", "wallet", "ip"],
    keep_hashes=True,
    max_cost_cents=100.0,
    include_code_sha=True,
    sign_attestations=False,
)
