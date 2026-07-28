from fastapi import FastAPI

from orchestration_service.app.api import router


app = FastAPI(title="MediAssist Orchestration Service", version="0.1.0")
app.include_router(router)
