"""AI worker access: `WorkerClient` (HTTP) or `MockWorkerClient` (AI_WORKER_URL=mock)."""

from app.ai.worker.client import WorkerClient, WorkerClientProtocol, get_worker_client
from app.ai.worker.mock import MockWorkerClient

__all__ = [
    "MockWorkerClient",
    "WorkerClient",
    "WorkerClientProtocol",
    "get_worker_client",
]
