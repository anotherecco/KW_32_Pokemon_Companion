from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import models
from database import SessionLocal1, SessionLocal2, engine1, engine2
import json
import os
import sqlite3
import time
import urllib.request
import urllib.error #der part den ich brauche um das error handeling beim seeding zu erreichen

# Create tables in the new database (DB2)
models.Base2.metadata.create_all(bind=engine2)

# FastAPI 0.95+ bevorzugt Lifespan-Handler statt der alten on_event()-Hooks.
# Damit starten und beenden wir Initialisierungen an einer klaren Stelle.
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_team_db_schema()

    try:
        if needs_pokemon_seed():
            seed_db(force=True)
    except Exception as exc:
        print(f"Startup seeding skipped: {exc}")

    yield

app = FastAPI(lifespan=lifespan)

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Dependencies for database sessions ---
def get_db1():
    db = SessionLocal1()
    try:
        yield db
    finally:
        db.close()


def get_db2():
    db = SessionLocal2()
    try:
        yield db
    finally:
        db.close()


# --- Pydantic schema for request validation ---
class ItemCreate(BaseModel):
    id: int
    name: str
    type: str
    no_damage_to: str
    half_damage_to: str
    double_damage_to: str
    no_damage_from: str
    half_damage_from: str
    double_damage_from: str


class Db2ItemCreate(BaseModel):
    pokemon_id: int


class Db2ItemUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None


def get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} for URL: {url}")
        return None
    except urllib.error.URLError as e:
        print(f"Network Error: {e.reason} for URL: {url}")
        return None
    except Exception as e:
        print(f"Json-Parsing Error: {str(e)} for URL: {url}")
        return None


def get_db_path():
    db_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(db_dir, "pokedex.db")


def get_sqlite_connection(db_path: str):
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def init_db():
    conn = get_sqlite_connection(get_db_path())
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pokemon (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                no_damage_to TEXT,
                half_damage_to TEXT,
                double_damage_to TEXT,
                no_damage_from TEXT,
                half_damage_from TEXT,
                double_damage_from TEXT
            )
            """
        )

        cursor.execute("PRAGMA table_info(pokemon)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        required_columns = {
            "name": "TEXT NOT NULL DEFAULT ''",
            "type": "TEXT NOT NULL DEFAULT ''",
            "no_damage_to": "TEXT DEFAULT ''",
            "half_damage_to": "TEXT DEFAULT ''",
            "double_damage_to": "TEXT DEFAULT ''",
            "no_damage_from": "TEXT DEFAULT ''",
            "half_damage_from": "TEXT DEFAULT ''",
            "double_damage_from": "TEXT DEFAULT ''",
        }
        for column_name, column_def in required_columns.items():
            if column_name not in existing_columns:
                cursor.execute(f"ALTER TABLE pokemon ADD COLUMN {column_name} {column_def}")

        conn.commit()
    finally:
        conn.close()


def needs_pokemon_seed():
    conn = get_sqlite_connection(get_db_path())
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pokemon'")
        if cursor.fetchone() is None:
            return True

        cursor.execute("PRAGMA table_info(pokemon)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        required_columns = {
            "name",
            "type",
            "no_damage_to",
            "half_damage_to",
            "double_damage_to",
            "no_damage_from",
            "half_damage_from",
            "double_damage_from",
        }
        if not required_columns.issubset(existing_columns):
            return True

        count = cursor.execute("SELECT COUNT(*) FROM pokemon").fetchone()[0]
        return count == 0
    finally:
        conn.close()


def ensure_team_db_schema():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "team_db.sqlite")
    if not os.path.exists(db_path):
        models.Base2.metadata.create_all(bind=engine2)
        return

    conn = get_sqlite_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='team_db'")
        if cursor.fetchone() is None:
            models.Base2.metadata.create_all(bind=engine2)
            return

        cursor.execute("PRAGMA table_info(team_db)")
        columns = [row[1] for row in cursor.fetchall()]
        if "status" not in columns:
            cursor.execute("ALTER TABLE team_db ADD COLUMN status TEXT DEFAULT 'neu'")
            conn.commit()
    finally:
        conn.close()


def _build_damage_lists(type_names: list[str], type_cache: dict):
    outgoing_effectiveness = {}
    incoming_effectiveness = {}

    for type_name in type_names:
        type_data = type_cache[type_name]

        for target in type_data.get("damage_relations", {}).get("double_damage_to", []):
            target_name = target["name"]
            outgoing_effectiveness[target_name] = outgoing_effectiveness.get(target_name, 1.0) * 2
        for target in type_data.get("damage_relations", {}).get("half_damage_to", []):
            target_name = target["name"]
            outgoing_effectiveness[target_name] = outgoing_effectiveness.get(target_name, 1.0) * 0.5
        for target in type_data.get("damage_relations", {}).get("no_damage_to", []):
            target_name = target["name"]
            outgoing_effectiveness[target_name] = 0.0

        for target in type_data.get("damage_relations", {}).get("double_damage_from", []):
            target_name = target["name"]
            incoming_effectiveness[target_name] = incoming_effectiveness.get(target_name, 1.0) * 2
        for target in type_data.get("damage_relations", {}).get("half_damage_from", []):
            target_name = target["name"]
            incoming_effectiveness[target_name] = incoming_effectiveness.get(target_name, 1.0) * 0.5
        for target in type_data.get("damage_relations", {}).get("no_damage_from", []):
            target_name = target["name"]
            incoming_effectiveness[target_name] = 0.0

    # Diese Hilfsfunktion gruppiert die Effektivitäten nach den drei relevanten Stufen.
    # Dadurch bleibt die Logik zentral und wir vermeiden doppelte Listenbildung.
    def categorize(effectiveness: dict[str, float], target_multiplier: float) -> list[str]:
        return [name for name, multiplier in sorted(effectiveness.items()) if multiplier == target_multiplier]

    def format_list(names: list[str]) -> str:
        return ",".join(names) if names else ""

    # Wir verwenden die gemeinsame Hilfsfunktion, damit die Liste immer konsistent aufgebaut wird.
    no_damage_to = categorize(outgoing_effectiveness, 0.0)
    half_damage_to = categorize(outgoing_effectiveness, 0.5)
    double_damage_to = categorize(outgoing_effectiveness, 2.0)
    no_damage_from = categorize(incoming_effectiveness, 0.0)
    half_damage_from = categorize(incoming_effectiveness, 0.5)
    double_damage_from = categorize(incoming_effectiveness, 2.0)

    return {
        "no_damage_to": format_list(no_damage_to),
        "half_damage_to": format_list(half_damage_to),
        "double_damage_to": format_list(double_damage_to),
        "no_damage_from": format_list(no_damage_from),
        "half_damage_from": format_list(half_damage_from),
        "double_damage_from": format_list(double_damage_from),
    }


def seed_db(force: bool = False):
    init_db()

    last_error = None
    for attempt in range(3):
        conn = get_sqlite_connection(get_db_path())
        try:
            cursor = conn.cursor()
            count = cursor.execute("SELECT COUNT(*) FROM pokemon").fetchone()[0]
            if count and not force:
                return {"status": "skipped", "count": count}

            if force:
                cursor.execute("DELETE FROM pokemon")

            type_cache = {}
            type_names = [
                "normal",
                "fire",
                "water",
                "grass",
                "electric",
                "ice",
                "fighting",
                "poison",
                "ground",
                "flying",
                "psychic",
                "bug",
                "rock",
                "ghost",
                "dragon",
                "dark",
                "steel",
                "fairy",
            ]
            for type_name in type_names:
                data = get_json(f"https://pokeapi.co/api/v2/type/{type_name}")
                if not data:
                    raise Exception(f"critical error: failed to fetch type data for {type_name}")
                type_cache[type_name] = data

            list_data = get_json("https://pokeapi.co/api/v2/pokemon?limit=100000&offset=0")
            if not isinstance(list_data, dict):
                raise RuntimeError("critical error: failed to fetch pokemon list metadata")

            for entry in list_data.get("results", []):
                pokemon_data = get_json(entry["url"])
                if not pokemon_data:
                    print(f"skipping pokemon {entry['name']} due to failed data fetch")
                    continue

                type_names_for_pokemon = [item["type"]["name"] for item in pokemon_data.get("types", [])]
                damage_lists = _build_damage_lists(type_names_for_pokemon, type_cache)
                cursor.execute(
                    """
                    INSERT INTO pokemon (
                        name,
                        type,
                        no_damage_to,
                        half_damage_to,
                        double_damage_to,
                        no_damage_from,
                        half_damage_from,
                        double_damage_from
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pokemon_data["name"],
                        ",".join(type_names_for_pokemon),
                        damage_lists["no_damage_to"],
                        damage_lists["half_damage_to"],
                        damage_lists["double_damage_to"],
                        damage_lists["no_damage_from"],
                        damage_lists["half_damage_from"],
                        damage_lists["double_damage_from"],
                    ),
                )
            conn.commit()
            final_count = cursor.execute("SELECT COUNT(*) FROM pokemon").fetchone()[0]
            return {"status": "success", "count": final_count}
        except sqlite3.OperationalError as db_err:
            conn.rollback()
            last_error = db_err
            if "locked" in str(db_err).lower() and attempt < 2:
                time.sleep(2)
                continue
            raise Exception(f"Database error during seeding: {str(db_err)}")
        except Exception as e:
            conn.rollback()
            raise Exception(f"Unexpected error during seeding: {str(e)}")
        finally:
            conn.close()

    raise Exception(f"Seeding failed after retries: {last_error}")


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/seed")
def seed_endpoint(force: bool = False):
    try:
        result = seed_db(force=force)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search-db1")
def search_db1(q: str):
    with engine1.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT id, name, type, no_damage_to, half_damage_to, double_damage_to, no_damage_from, half_damage_from, double_damage_from "
                "FROM pokemon WHERE name LIKE :q ORDER BY name LIMIT 50"
            ),
            {"q": f"%{q}%"},
        ).mappings().all()
    return [
        {
            "id": row["id"],
            "title": row["name"],
            "type": row["type"],
            "no_damage_to": row["no_damage_to"],
            "half_damage_to": row["half_damage_to"],
            "double_damage_to": row["double_damage_to"],
            "no_damage_from": row["no_damage_from"],
            "half_damage_from": row["half_damage_from"],
            "double_damage_from": row["double_damage_from"],
        }
        for row in rows
    ]


@app.get("/db2")
def read_db2(db2: Session = Depends(get_db2)):
    items = db2.query(models.team_managment_db).order_by(models.team_managment_db.id).all()
    return [
        {
            "id": item.id,
            "title": item.name,
            "type": item.type,
            "status": item.status,
            "no_damage_to": item.no_damage_to,
            "half_damage_to": item.half_damage_to,
            "double_damage_to": item.double_damage_to,
            "no_damage_from": item.no_damage_from,
            "half_damage_from": item.half_damage_from,
            "double_damage_from": item.double_damage_from,
        }
        for item in items
    ]


@app.post("/db2")
def create_db2_item(item: Db2ItemCreate, db2: Session = Depends(get_db2)):
    if db2.query(models.team_managment_db).count() >= 6:
        raise HTTPException(status_code=400, detail="Only 6 team slots are allowed")

    existing_ids = {row[0] for row in db2.query(models.team_managment_db.id).all()}
    available_id = next((slot for slot in range(1, 7) if slot not in existing_ids), None)
    if available_id is None:
        raise HTTPException(status_code=400, detail="No team slots available")

    with engine1.connect() as conn:
        pokemon = conn.execute(
            text(
                "SELECT name, type, no_damage_to, half_damage_to, double_damage_to, no_damage_from, half_damage_from, double_damage_from "
                "FROM pokemon WHERE id = :id"
            ),
            {"id": item.pokemon_id},
        ).mappings().first()

    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokemon not found in DB1")

    db_item = models.team_managment_db(
        id=available_id,
        name=pokemon["name"],
        type=pokemon["type"],
        status="ready to fight",
        no_damage_to=pokemon["no_damage_to"] or "",
        half_damage_to=pokemon["half_damage_to"] or "",
        double_damage_to=pokemon["double_damage_to"] or "",
        no_damage_from=pokemon["no_damage_from"] or "",
        half_damage_from=pokemon["half_damage_from"] or "",
        double_damage_from=pokemon["double_damage_from"] or "",
    )
    db2.add(db_item)
    db2.commit()
    db2.refresh(db_item)

    return {
        "id": db_item.id,
        "title": db_item.name,
        "type": db_item.type,
        "status": db_item.status,
        "no_damage_to": db_item.no_damage_to,
        "half_damage_to": db_item.half_damage_to,
        "double_damage_to": db_item.double_damage_to,
        "no_damage_from": db_item.no_damage_from,
        "half_damage_from": db_item.half_damage_from,
        "double_damage_from": db_item.double_damage_from,
    }


@app.put("/db2/{item_id}")
def update_db2_item(item_id: int, item: Db2ItemUpdate, db2: Session = Depends(get_db2)):
    db_item = db2.query(models.team_managment_db).filter(models.team_managment_db.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.title is not None and item.title != "":
        db_item.name = item.title

    if item.status is not None:
        db_item.status = item.status
    else:
        db_item.status = "defeated" if db_item.status == "ready to fight" else "ready to fight"

    db2.commit()
    db2.refresh(db_item)

    return {"id": db_item.id, "title": db_item.name, "status": db_item.status}


@app.delete("/db2/{item_id}")
def delete_db2_item(item_id: int, db2: Session = Depends(get_db2)):
    """Delete a team entry using the same route the frontend already calls."""
    # The React client sends DELETE requests to /db2/{id}, so this handler must exist
    # even though the older /items/{id} endpoint is still kept for compatibility.
    db_item = db2.query(models.team_managment_db).filter(models.team_managment_db.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db2.delete(db_item)
    db2.commit()

    return {"message": "Item successfully deleted"}


@app.post("/items/")
def create_item(item: ItemCreate, db2: Session = Depends(get_db2)):
    """Store one team entry in DB2. Only 6 slots are allowed."""
    if not 1 <= item.id <= 6:
        raise HTTPException(status_code=400, detail="Team slots must be between 1 and 6")

    if db2.query(models.team_managment_db).count() >= 6:
        raise HTTPException(status_code=400, detail="Only 6 team slots are allowed")

    existing = db2.query(models.team_managment_db).filter(models.team_managment_db.id == item.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="That slot is already taken")

    db_item = models.team_managment_db(
        id=item.id,
        name=item.name,
        type=item.type,
        no_damage_to=item.no_damage_to,
        half_damage_to=item.half_damage_to,
        double_damage_to=item.double_damage_to,
        no_damage_from=item.no_damage_from,
        half_damage_from=item.half_damage_from,
        double_damage_from=item.double_damage_from,
    )
    db2.add(db_item)
    db2.commit()
    db2.refresh(db_item)

    return db_item



