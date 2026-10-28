from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import random
import string
from typing import Dict, Optional

app = FastAPI(title="GO PORTUGUESE! Server", version="1.0.0")

# Para produção, restrinja allow_origins aos domínios reais do seu frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Salas ficam apenas na memória deste processo e podem ser perdidas ao reiniciar.
ROOMS_DB: Dict[str, dict] = {}

# Configure a variável de ambiente TEACHER_PIN no Render antes de publicar.
import os
TEACHER_PIN = os.getenv("TEACHER_PIN", "adm@437")


class CreateRoomRequest(BaseModel):
    pin: str


class JoinRoomRequest(BaseModel):
    room_code: str = Field(min_length=5, max_length=5)
    player_name: str = Field(min_length=1, max_length=40)
    avatar: dict = Field(default_factory=dict)


class UpdateScoreRequest(BaseModel):
    room_code: str = Field(min_length=5, max_length=5)
    player_name: str = Field(min_length=1, max_length=40)
    score: int = Field(ge=0)
    completed: bool
    time_seconds: Optional[int] = Field(default=0, ge=0)


class StartRoomRequest(BaseModel):
    room_code: str = Field(min_length=5, max_length=5)
    pin: str


@app.get("/")
def read_root():
    return {"status": "online", "game": "GO PORTUGUESE!", "version": "1.0.0"}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


def require_teacher_pin(pin: str):
    if pin != TEACHER_PIN:
        raise HTTPException(status_code=403, detail="PIN do professor incorreto")


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
        raise HTTPException(status_code=503, detail="Não foi possível gerar um código. Tente novamente.")

    ROOMS_DB[room_code] = {
        "room_code": room_code,
        "status": "WAITING",
        "players": {},
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
    }
    return {"success": True, "room_code": code, "status": room["status"]}


@app.post("/api/rooms/start")
def start_room(req: StartRoomRequest):
    require_teacher_pin(req.pin)
    room = ROOMS_DB.get(req.room_code)
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    room["status"] = "IN_GAME"
    return {"success": True, "message": "Partida iniciada!"}


@app.get("/api/rooms/{room_code}/status")
def get_room_status(room_code: str):
    room = ROOMS_DB.get(room_code)
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    players = sorted(room["players"].values(), key=lambda player: player["score"], reverse=True)
    return {
        "room_code": room_code,
        "status": room["status"],
        "players": players,
    }


@app.post("/api/rooms/update_score")
def update_score(req: UpdateScoreRequest):
    room = ROOMS_DB.get(req.room_code)
    if not room or req.player_name not in room["players"]:
        raise HTTPException(status_code=404, detail="Jogador ou sala não encontrados")
    player = room["players"][req.player_name]
    player["score"] = req.score
    player["completed"] = req.completed
    player["time_seconds"] = req.time_seconds or 0
    return {"success": True}
