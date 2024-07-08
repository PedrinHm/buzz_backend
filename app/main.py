from fastapi import FastAPI
from .routers.auth import router as auth_router  
from .config.database import engine
from .models.user import Base, User

app = FastAPI()

app.include_router(auth_router)

def create_tables():
    Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def startup_event():
    create_tables()