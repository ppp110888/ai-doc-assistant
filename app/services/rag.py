from app.services.llm import ask_deepseek
from app.services.retrieval import retrieve_chunks


NO_CONTEXT_ANSWER = "知识库中没有找到相关内容。"


def answer_question(
    question: str,
    limit: int = 3,
) -> dict:
    sources = retrieve_chunks(
        question=question,
        limit=limit,
    )

    if not sources:
        return {
            "answer": NO_CONTEXT_ANSWER,
            "sources": [],
        }

    context = "\n\n".join(
        f"[来源 {index}] {source['text']}"
        for index, source in enumerate(
            sources,
            start=1,
        )
    )

    prompt = f"""
请严格根据参考资料回答问题。

要求：
1. 不要使用参考资料之外的信息。
2. 如果参考资料无法回答，明确说“知识库中没有找到相关内容”。
3. 使用简洁、准确的中文回答。

问题：
{question}

参考资料：
{context}
""".strip()

    answer = ask_deepseek(prompt)

    return {
        "answer": answer,
        "sources": sources,
    }