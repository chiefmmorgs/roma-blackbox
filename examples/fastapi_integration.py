"""FastAPI integration example with roma-blackbox"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import logging

from roma_blackbox import BlackBoxWrapper, Policy

logging.basicConfig(level=logging.INFO)


class MockROMAAgent:
    async def run(self, task: str, **kwargs):
        return {
            "result": {"summary": f"Completed: {task}", "findings": ["Finding 1", "Finding 2"]},
            "traces": {"planner": {"subtasks": ["research"]}, "executor": {"steps": ["step1"]}},
            "cost": 2.5,
        }


class RunRequest(BaseModel):
    request_id: str
    task: str
    payload: Optional[Dict[str, Any]] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    agent = MockROMAAgent()
    policy = Policy(black_box=True, pii_fields=["email", "wallet", "ip"])
    app.state.blackbox_agent = BlackBoxWrapper(agent, policy, storage="memory", code_sha="v1.0.0")
    print("✓ ROMA agent wrapped with black-box monitoring")
    yield


app = FastAPI(title="ROMA Black-Box API", version="1.0.0", lifespan=lifespan)


@app.get("/")
async def root():
    return {
        "service": "ROMA Black-Box API",
        "version": "1.0.0",
        "endpoints": {
            "run": "POST /run",
            "health": "GET /health",
            "outcome": "GET /outcome/{request_id}",
        },
    }


@app.post("/run")
async def run_agent(request: RunRequest):
    try:
        result = await app.state.blackbox_agent.run(
            request_id=request.request_id, task=request.task, payload=request.payload or {}
        )
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy", "agent_ready": hasattr(app.state, "blackbox_agent")}


@app.get("/outcome/{request_id}")
async def get_outcome(request_id: str):
    outcome = await app.state.blackbox_agent.get_outcome(request_id)
    if outcome is None:
        raise HTTPException(status_code=404, detail="Outcome not found")
    return outcome


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting ROMA Black-Box API")
    print("  • http://localhost:8000")
    print("  • http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
