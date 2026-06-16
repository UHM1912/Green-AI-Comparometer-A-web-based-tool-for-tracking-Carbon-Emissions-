import logging
import app.core.logging_config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.connection import init_db
from app.api.auth import router as auth_router
from app.api.refactor import router as refactor_router

logger = logging.getLogger("EcoRefactor.main")

app = FastAPI(
    title="EcoRefactor API",
    description="AI-powered green code refactoring and carbon benchmarking API",
    version="1.0.0"
)

# Set up CORS so the Angular frontend can query the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lifespan startup sequence to initialize DB tables
@app.on_event("startup")
def startup_db():
    logger.info("Initializing EcoRefactor database tables...")
    init_db()


# Mount API Routers
app.include_router(auth_router)
app.include_router(refactor_router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "EcoRefactor",
        "description": "Green computing LLM optimizer API is active."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
