from fastapi import FastAPI
from app.v1.common.middleware import middleware
from app.v1.common.error.exception_handler import exception_handler
from app.v1.domain.recommendation.router import recommend_router
from app.v1.domain.chat.router.chating import chat_router
from app.v1.domain.chat.router.get_img import img_router

app = FastAPI()

middleware(app)

exception_handler(app)
app.include_router(recommend_router)
app.include_router(chat_router)
app.include_router(img_router)