from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.local_test_version.db.session import SessionDep
from app.local_test_version.db.schemas import User, Conversation ,Role, Message
from app.local_test_version.db.models import Chat, Con
from app.local_test_version.services.llm.generator import bookshelf_llm_service

chat_router = APIRouter()


@chat_router.post("/make_chat")
async def make_chat(session: SessionDep, con: Con):
    stmt = select(User).where(User.id == con.user_id)
    result = session.exec(stmt).first()
    if not result:
        raise HTTPException(status_code=404, detail="no user")

    dict_con = con.model_dump()
    db_con = Conversation.model_validate(dict_con)

    session.add(db_con)
    session.commit()
    session.refresh(db_con)
    return db_con


@chat_router.post("/chat")
async def chatbot(session: SessionDep, chat: Chat):
    result = session.get(User, chat.user_id)
    if not result:
        raise HTTPException(status_code=404, detail="no user")
    con_stmt = select(Conversation).where(Conversation.id == chat.con_id).where(Conversation.user_id == result.id)
    con_result = session.exec(con_stmt).first()
    if not con_result:
        raise HTTPException(status_code=404, detail="no conversation")

    answer = bookshelf_llm_service.bookshelf_model(session, chat.con_id, chat.question, 15, 6)
    session.add(Message(conversation_id=chat.con_id, role=Role.user ,content=chat.question))
    try:
        # if isinstance(answer, dict):
        #     content = answer.get("answer", "")
        # else:
        #     content = getattr(answer, "answer", str(answer))
        session.add(Message(conversation_id=chat.con_id, role=Role.assistant, content=answer.get("answer", "")))
    except AttributeError as e:
        print(e)
        session.add(Message(conversation_id=chat.con_id, role=Role.assistant, content=answer))
    session.commit()
    return answer