from app.services import rag


def test_answer_question(monkeypatch):
    sources = [{
        "text": "系统使用 BAAI/bge-small-zh-v1.5 模型。",
        "file_id": 27,
        "chunk_index": 0,
        "distance": 0.12,
    }]

    monkeypatch.setattr(
        rag,
        "retrieve_chunks",
        lambda question, limit: sources,
    )

    captured = {}

    def fake_ask_deepseek(prompt):
        captured["prompt"] = prompt
        return "系统使用 BAAI/bge-small-zh-v1.5 模型。"

    monkeypatch.setattr(
        rag,
        "ask_deepseek",
        fake_ask_deepseek,
    )

    result = rag.answer_question(
        "系统使用什么向量模型？",
        limit=3,
    )

    assert result["answer"] == (
        "系统使用 BAAI/bge-small-zh-v1.5 模型。"
    )
    assert result["sources"] == sources
    assert "系统使用什么向量模型" in captured["prompt"]
    assert "BAAI/bge-small-zh-v1.5" in captured["prompt"]


def test_answer_question_without_sources(monkeypatch):
    monkeypatch.setattr(
        rag,
        "retrieve_chunks",
        lambda question, limit: [],
    )

    def fail_if_called(prompt):
        raise AssertionError(
            "DeepSeek should not be called"
        )

    monkeypatch.setattr(
        rag,
        "ask_deepseek",
        fail_if_called,
    )

    result = rag.answer_question("不存在的信息")

    assert result == {
        "answer": "知识库中没有找到相关内容。",
        "sources": [],
    }