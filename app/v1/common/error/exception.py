from app.v1.common.error.base_exception import BaseAppException

class MemberNotFoundException(BaseAppException):
    def __init__(self, username: str):
        super().__init__(404, f"회원을 찾을 수 없습니다: {username}")


class SessionNotFoundException(BaseAppException):
    def __init__(self, session_id: int):
        super().__init__(404, f"세션을 찾을 수 없습니다: {session_id}")


class LLMServiceException(BaseAppException):
    def __init__(self):
        super().__init__(500, "AI 서비스에 문제가 발생했습니다.")

class MessageNotFoundException(BaseAppException):
    def __init__(self, message_id: int):
        super().__init__(404, f"해당 메시지를 찾을 수 없습니다. {message_id}")