from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
import os

load_dotenv()

# Configuração da conexão com o banco de dados
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Importar o Base dos modelos
from app.config.database import Base

# Importar modelos
from app.models.user import User
from app.models.user_type import UserType, UserTypeNames
from app.models.bus import Bus
from app.models.bus_stop import BusStop

# Importar roteadores
from app.routers import auth, users, buses, bus_stops

app = FastAPI()

# Incluir roteadores
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(buses.router)
app.include_router(bus_stops.router)

def create_tables():
    Base.metadata.create_all(bind=engine)

def create_user_types(session: Session):
    if not session.query(UserType).first():
        user_types = [
            UserType(description=UserTypeNames.STUDENT),
            UserType(description=UserTypeNames.DRIVER),
            UserType(description=UserTypeNames.ADMIN),
        ]
        session.add_all(user_types)
        session.commit()

@app.on_event("startup")
async def startup_event():
    create_tables()  
    with SessionLocal() as session:
        create_user_types(session)

@app.on_event("shutdown")
async def shutdown_event():
    db = SessionLocal()
    db.close()
