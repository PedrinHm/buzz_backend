from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from .models.user_type import UserType, UserTypeNames
from .routers import users, buses, bus_stops, auth, trips, student_trips, trip_bus_stops
from .models import bus, user, trip, student_trip, trip_bus_stop


load_dotenv()

# Configuração da conexão com o banco de dados
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Importar o Base dos modelos
from app.config.database import Base

# Importar modelos
from app.models.user import User
from app.models.user_type import UserType

app = FastAPI()


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(buses.router)
app.include_router(bus_stops.router)
app.include_router(trips.router)
app.include_router(student_trips.router)
app.include_router(trip_bus_stops.router)

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

