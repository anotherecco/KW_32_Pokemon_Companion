import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# DB1: read-only reference data for the Pokedex API.
SQLALCHEMY_DATABASE_URL_1 = f"sqlite:///{os.path.join(BASE_DIR, 'pokedex.db')}"
engine1 = create_engine(SQLALCHEMY_DATABASE_URL_1, connect_args={"check_same_thread": False})
SessionLocal1 = sessionmaker(bind=engine1, autocommit=False, autoflush=False)
Base1 = declarative_base()

# DB2: writable team storage. Only 6 slots are allowed.
SQLALCHEMY_DATABASE_URL_2 = f"sqlite:///{os.path.join(BASE_DIR, 'team_db.sqlite')}"
engine2 = create_engine(SQLALCHEMY_DATABASE_URL_2, connect_args={"check_same_thread": False})
SessionLocal2 = sessionmaker(bind=engine2, autocommit=False, autoflush=False)
Base2 = declarative_base()