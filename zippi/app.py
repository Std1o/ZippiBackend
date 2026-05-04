from fastapi import FastAPI

from zippi.api import router

app = FastAPI()
app.include_router(router)