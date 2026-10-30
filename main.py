import os
import random
import string
import time
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

app = FastAPI(title="GO PORTUGUESE! Server", version="1.0.0")

# Permitir CORS de qualquer origem para conexões no Render, redes locais e celulares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Salas ficam em memória (1 worker Gunicorn no Render)
ROOMS_DB: Dict[str, dict] = {}

# Variável de ambiente TEACHER_PIN (padrão: adm@437)
TEACHER_PIN = os.getenv("TEACHER_PIN", "adm@437")


class VerifyPinRequest(BaseModel):
    pin: str


class CreateRoomRequest(BaseModel):
    pin: str


class JoinRoomRequest(BaseModel):
    room_code: str = Field(min_length=1, max_length=10)
    player_name: str = Field(min_length=1, max_length=50)
    avatar: dict = Field(default_factory=dict)


class LeaveRoomRequest(BaseModel):
    room_code: str = Field(min_length=1, max_length=10)
    player_name: str = Field(min_length=1, max_length=50)


class UpdateScoreRequest(BaseModel):
    room_code: str = Field(min_length=1, max_length=10)
    player_name: str = Field(min_length=1, max_length=50)
    score: int = Field(ge=0)
    completed: bool
    time_seconds: Optional[int] = Field(default=0, ge=0)


class StartRoomRequest(BaseModel):
    room_code: str = Field(min_length=1, max_length=10)
    pin: str


@app.get("/")
def read_root():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"status": "online", "game": "GO PORTUGUESE!", "version": "1.0.0"}


@app.get("/game")
def read_game():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    raise HTTPException(status_code=404, detail="Arquivo index.html não encontrado")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/status")
def api_status():
    return {
        "status": "online",
        "game": "GO PORTUGUESE!",
        "version": "1.0.0",
        "active_rooms": len(ROOMS_DB),
    }


def require_teacher_pin(pin: str):
    if pin.strip() != TEACHER_PIN.strip():
        raise HTTPException(status_code=403, detail="PIN do professor incorreto")


@app.post("/api/teacher/verify")
def verify_teacher_pin(req: VerifyPinRequest):
    require_teacher_pin(req.pin)
    return {"success": True, "message": "PIN correto"}


@app.post("/api/rooms/create")
def create_room(req: CreateRoomRequest):
    require_teacher_pin(req.pin)
    room_code = ""
    for _ in range(100):
        candidate = "".join(random.choices(string.digits, k=5))
        if candidate not in ROOMS_DB:
            room_code = candidate
            break
    if not room_code:
        raise HTTPException(
            status_code=503,
            detail="Não foi possível gerar um código de sala. Tente novamente.",
        )

    ROOMS_DB[room_code] = {
        "room_code": room_code,
        "status": "WAITING",
        "players": {},
        "created_at": time.time(),
        "force_finish": False,
    }
    return {"success": True, "room_code": room_code}


@app.post("/api/rooms/join")
def join_room(req: JoinRoomRequest):
    code = req.room_code.strip()
    if code not in ROOMS_DB:
        raise HTTPException(status_code=404, detail="Código da sala não encontrado!")
    name = req.player_name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Informe o nome do jogador.")
    room = ROOMS_DB[code]
    room["players"][name] = {
        "name": name,
        "score": 0,
        "completed": False,
        "time_seconds": 0,
        "avatar": req.avatar,
        "last_seen": time.time(),
    }
    return {"success": True, "room_code": code, "status": room["status"]}


@app.post("/api/rooms/leave")
def leave_room(req: LeaveRoomRequest):
    code = req.room_code.strip()
    room = ROOMS_DB.get(code)
    if room and req.player_name in room["players"]:
        del room["players"][req.player_name]
    return {"success": True, "message": "Jogador saiu da sala"}


@app.post("/api/rooms/start")
def start_room(req: StartRoomRequest):
    require_teacher_pin(req.pin)
    code = req.room_code.strip()
    room = ROOMS_DB.get(code)
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    room["status"] = "IN_GAME"
    room["force_finish"] = False
    return {"success": True, "message": "Partida iniciada!"}


@app.post("/api/rooms/force_finish")
def force_finish_room(req: StartRoomRequest):
    require_teacher_pin(req.pin)
    code = req.room_code.strip()
    room = ROOMS_DB.get(code)
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    room["force_finish"] = True
    return {"success": True, "message": "Pódio liberado pelo professor"}


@app.get("/api/rooms/{room_code}/status")
def get_room_status(room_code: str):
    code = room_code.strip()
    room = ROOMS_DB.get(code)
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")

    now = time.time()
    # Remove jogadores inativos por mais de 35 segundos para não travar o pódio se fecharam o jogo
    stale_players = [
        name
        for name, p in room["players"].items()
        if now - p.get("last_seen", now) > 35
    ]
    for name in stale_players:
        del room["players"][name]

    active_players = list(room["players"].values())
    total_players = len(active_players)
    completed_players = sum(1 for p in active_players if p.get("completed", False))

    all_completed = (
        (total_players > 0 and completed_players >= total_players)
        or room.get("force_finish", False)
    )

    # Ordenação por maior pontuação e menor tempo total gasto
    players = sorted(
        active_players,
        key=lambda player: (player["score"], -player.get("time_seconds", 0)),
        reverse=True,
    )

    return {
        "room_code": code,
        "status": room["status"],
        "all_completed": all_completed,
        "total_players": total_players,
        "completed_players": completed_players,
        "players": players,
    }


@app.post("/api/rooms/update_score")
def update_score(req: UpdateScoreRequest):
    code = req.room_code.strip()
    room = ROOMS_DB.get(code)
    if not room or req.player_name not in room["players"]:
        raise HTTPException(status_code=404, detail="Jogador ou sala não encontrados")
    player = room["players"][req.player_name]
    player["score"] = req.score
    player["completed"] = req.completed
    player["time_seconds"] = req.time_seconds or 0
    player["last_seen"] = time.time()
    return {"success": True}


@app.post("/api/rooms/reset")
def reset_room(req: StartRoomRequest):
    require_teacher_pin(req.pin)
    code = req.room_code.strip()
    if code in ROOMS_DB:
        del ROOMS_DB[code]
    return {"success": True, "message": "Sala removida/reiniciada com sucesso"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Iniciando servidor local GO PORTUGUESE! em http://localhost:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
