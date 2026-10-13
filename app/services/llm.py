import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def get_deepseek_client() -> OpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv(
        "DEEPSEEK_BASE_URL",
        "https://api.deepseek.com",
    )

    if not api_key or api_key == "your-api-key-here":
        raise RuntimeError(
            "DEEPSEEK_API_KEY is not configured. "
            "Please set it in the .env file."
        )

    return OpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=30.0,
    max_retries=2,
    )



def ask_deepseek(question: str) -> str:
    client = get_deepseek_client()

    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "你是一个 helpful 的中文 AI 助手。",
            },
            {
                "role": "user",
                "content": question,
            },
        ],
        temperature=0.2,
    )

    answer = response.choices[0].message.content

    if not answer:
        raise RuntimeError("DeepSeek returned an empty response.")

    return answer