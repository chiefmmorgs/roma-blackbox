"""Storage abstraction for outcomes and audit logs"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class AbstractStorage(ABC):
    """Abstract base class for outcome storage"""

    @abstractmethod
    async def store_outcome(self, outcome: Dict):
        pass

    @abstractmethod
    async def get_outcome(self, request_id: str) -> Optional[Dict]:
        pass

    @abstractmethod
    async def log_audit_event(self, event: Dict):
        pass

    @abstractmethod
    async def get_audit_log(self, request_id: str) -> List[Dict]:
        pass


class MemoryStorage(AbstractStorage):
    """In-memory storage for testing"""

    def __init__(self):
        self.outcomes = {}
        self.audit_log = []
        logger.info("MemoryStorage initialized")

    async def store_outcome(self, outcome: Dict):
        request_id = outcome["request_id"]
        self.outcomes[request_id] = outcome

    async def get_outcome(self, request_id: str) -> Optional[Dict]:
        return self.outcomes.get(request_id)

    async def log_audit_event(self, event: Dict):
        self.audit_log.append(event)

    async def get_audit_log(self, request_id: str) -> List[Dict]:
        return [e for e in self.audit_log if e.get("request_id") == request_id]


class PostgreSQLStorage(AbstractStorage):
    """PostgreSQL storage backend"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._pool = None

    async def _get_pool(self):
        if self._pool is None:
            import asyncpg

            self._pool = await asyncpg.create_pool(self.connection_string)
        return self._pool

    async def store_outcome(self, outcome: Dict):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO outcomes 
                (request_id, input_hash, output_hash, status, latency_ms, cost_cents, created_at, attestation)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (request_id) DO UPDATE SET status = EXCLUDED.status
                """,
                outcome["request_id"],
                outcome.get("input_hash"),
                outcome.get("output_hash"),
                outcome["status"],
                outcome.get("latency_ms"),
                outcome.get("cost_cents"),
                outcome.get("created_at"),
                json.dumps(outcome.get("attestation", {})),
            )

    async def get_outcome(self, request_id: str) -> Optional[Dict]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM outcomes WHERE request_id = $1", request_id)
            return dict(row) if row else None

    async def log_audit_event(self, event: Dict):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO audit_log (request_id, action, reason, timestamp) VALUES ($1, $2, $3, $4)",
                event["request_id"],
                event["action"],
                event.get("reason"),
                event.get("timestamp"),
            )

    async def get_audit_log(self, request_id: str) -> List[Dict]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM audit_log WHERE request_id = $1 ORDER BY timestamp DESC", request_id
            )
            return [dict(row) for row in rows]


class JSONFileStorage(AbstractStorage):
    """Simple JSON file storage"""

    def __init__(self, filepath: str = "outcomes.json"):
        self.filepath = filepath
        self._load_data()

    def _load_data(self):
        try:
            with open(self.filepath, "r") as f:
                data = json.load(f)
                self.outcomes = data.get("outcomes", {})
                self.audit_log = data.get("audit_log", [])
        except FileNotFoundError:
            self.outcomes = {}
            self.audit_log = []

    def _save_data(self):
        with open(self.filepath, "w") as f:
            json.dump({"outcomes": self.outcomes, "audit_log": self.audit_log}, f, indent=2)

    async def store_outcome(self, outcome: Dict):
        self.outcomes[outcome["request_id"]] = outcome
        self._save_data()

    async def get_outcome(self, request_id: str) -> Optional[Dict]:
        return self.outcomes.get(request_id)

    async def log_audit_event(self, event: Dict):
        self.audit_log.append(event)
        self._save_data()

    async def get_audit_log(self, request_id: str) -> List[Dict]:
        return [e for e in self.audit_log if e.get("request_id") == request_id]


def get_storage(storage_string: str) -> AbstractStorage:
    if storage_string == "memory":
        return MemoryStorage()
    elif storage_string.startswith("postgresql://"):
        return PostgreSQLStorage(storage_string)
    elif storage_string.endswith(".json"):
        return JSONFileStorage(storage_string)
    else:
        raise ValueError(f"Unknown storage type: {storage_string}")
