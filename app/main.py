import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.agent import StudyAgent
from app.config import get_settings
from app.database import GraphDatabase
from app.logging_config import configure_logging
from app.repository import StudyRepository
from app.schemas import ActionResponse, ChatRequest, ChatResponse, ConfirmRequest
from app.tools import ActionService

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)
database = GraphDatabase(settings)
repository = StudyRepository(database)
actions = ActionService(repository)
agent = StudyAgent(repository, actions, settings)

app = FastAPI(title="Study Copilot", version="0.1.0")
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": database.health()}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        return ChatResponse(**agent.respond(request.user_id, request.message))
    except Exception as exc:
        logger.exception("Agent request failed")
        raise HTTPException(status_code=503, detail="The study graph is temporarily unavailable") from exc


@app.post("/api/actions/{action_id}/confirm", response_model=ActionResponse)
def confirm(action_id: str, request: ConfirmRequest) -> ActionResponse:
    try:
        result = actions.confirm(action_id, request.approved)
        return ActionResponse(action_id=action_id, status=result["status"], result=result["result"])
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Action confirmation failed")
        raise HTTPException(status_code=503, detail="The study graph is temporarily unavailable") from exc
