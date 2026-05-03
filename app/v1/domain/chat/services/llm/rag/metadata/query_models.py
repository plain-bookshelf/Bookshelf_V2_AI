from app.v1.config import settings
from openai import OpenAI


class QueryRouter:
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.BASE_URL,
            api_key=settings.SMALL_API_KEY
        )

    def get_response(self, user_query: str, prompt: str, model: str) -> str:

        resp = self.client.responses.create(
            model=model,
            instructions=prompt,
            input=f"query:\n{user_query}",
        )
        answer = resp.output_text
        return answer


    def sim_response(self, user_query: str, prompt: str) -> bool:
        answer = self.get_response(user_query, prompt, model=settings.MODEL_2)
        print(answer)
        if answer == 'True':
            return True
        else:
            return False


query_router = QueryRouter()