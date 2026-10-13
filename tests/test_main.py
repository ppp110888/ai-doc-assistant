from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_txt_file():
    response = client.post(
        "/upload",
        files={
            "file": (
                "test.txt",
                BytesIO(b"hello ai engineer"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["content_type"] == "text/plain"
    assert data["size"] == len(b"hello ai engineer")
    assert "id" in data


def test_reject_unsupported_file_type():
    response = client.post(
        "/upload",
        files={
            "file": (
                "image.jpg",
                BytesIO(b"fake image"),
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 400


def test_file_not_found():
    response = client.get("/files/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "File record not found"}

def test_chat_success(monkeypatch):
    def fake_ask_deepseek(question: str) -> str:
        return f"模拟回答：{question}"

    monkeypatch.setattr(
        "app.main.ask_deepseek",
        fake_ask_deepseek,
    )

    response = client.post(
        "/chat",
        json={"question": "什么是 FastAPI？"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["question"] == "什么是 FastAPI？"
    assert data["answer"] == "模拟回答：什么是 FastAPI？"


def test_chat_reject_empty_question():
    response = client.post(
        "/chat",
        json={"question": "   "},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Question must not be empty",
    }


def test_chat_handles_deepseek_error(monkeypatch):
    def fake_ask_deepseek(question: str) -> str:
        raise RuntimeError("simulated DeepSeek error")

    monkeypatch.setattr(
        "app.main.ask_deepseek",
        fake_ask_deepseek,
    )

    response = client.post(
        "/chat",
        json={"question": "测试错误处理"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "DeepSeek request failed",
    }

def test_index_file_success(monkeypatch):
    upload_response = client.post(
        "/upload",
        files={
            "file": (
                "index-test.txt",
                BytesIO(b"document content"),
                "text/plain",
            )
        },
    )
    file_id = upload_response.json()["id"]

    monkeypatch.setattr(
        "app.main.index_document",
        lambda file_id, file_path: 3,
    )

    response = client.post(
        f"/files/{file_id}/index"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["file_id"] == file_id
    assert data["filename"] == "index-test.txt"
    assert data["chunk_count"] == 3
    assert data["status"] == "indexed"
    assert data["is_indexed"] is True
    assert isinstance(data["indexed_at"], str)


def test_index_file_not_found():
    response = client.post(
        "/files/999999/index"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "File record not found",
    }


def test_index_file_rejects_empty_document(monkeypatch):
    upload_response = client.post(
        "/upload",
        files={
            "file": (
                "empty.txt",
                BytesIO(b""),
                "text/plain",
            )
        },
    )
    file_id = upload_response.json()["id"]

    def fake_index_document(file_id, file_path):
        raise ValueError(
            "Document contains no extractable text"
        )

    monkeypatch.setattr(
        "app.main.index_document",
        fake_index_document,
    )

    response = client.post(
        f"/files/{file_id}/index"
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Document contains no extractable text",
    }

def test_search_success(monkeypatch):
    monkeypatch.setattr(
        "app.main.retrieve_chunks",
        lambda question, limit: [{
            "text": "向量模型是 BGE",
            "file_id": 27,
            "chunk_index": 0,
            "distance": 0.12,
        }],
    )

    response = client.post(
        "/search",
        json={
            "question": "系统使用什么向量模型？",
            "limit": 3,
        },
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["file_id"] == 27


def test_search_rejects_empty_question():
    response = client.post(
        "/search",
        json={
            "question": "   ",
            "limit": 3,
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Question must not be empty",
    }


def test_search_rejects_invalid_limit():
    response = client.post(
        "/search",
        json={
            "question": "测试问题",
            "limit": 0,
        },
    )

    assert response.status_code == 422

def test_ask_success(monkeypatch):
    monkeypatch.setattr(
        "app.main.answer_question",
        lambda question, limit: {
            "answer": "系统使用 BGE 中文向量模型。",
            "sources": [{
                "text": "系统使用 BGE 中文向量模型。",
                "file_id": 27,
                "chunk_index": 0,
                "distance": 0.12,
            }],
        },
    )

    response = client.post(
        "/ask",
        json={
            "question": "系统使用什么向量模型？",
            "limit": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data["history_id"], int)
    assert data["question"] == "系统使用什么向量模型？"
    assert data["answer"] == "系统使用 BGE 中文向量模型。"
    assert data["sources"][0]["file_id"] == 27


def test_ask_rejects_empty_question(monkeypatch):
    def fake_answer_question(question, limit):
        raise ValueError("Question must not be empty")

    monkeypatch.setattr(
        "app.main.answer_question",
        fake_answer_question,
    )

    response = client.post(
        "/ask",
        json={
            "question": "   ",
            "limit": 3,
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Question must not be empty",
    }


def test_ask_handles_service_error(monkeypatch):
    def fake_answer_question(question, limit):
        raise RuntimeError("simulated service error")

    monkeypatch.setattr(
        "app.main.answer_question",
        fake_answer_question,
    )

    response = client.post(
        "/ask",
        json={
            "question": "测试问题",
            "limit": 3,
        },
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Knowledge base question failed",
    }

def test_list_history(monkeypatch):
    monkeypatch.setattr(
        "app.main.answer_question",
        lambda question, limit: {
            "answer": "测试答案",
            "sources": [{
                "text": "测试来源",
                "file_id": 27,
                "chunk_index": 0,
                "distance": 0.1,
            }],
        },
    )

    ask_response = client.post(
        "/ask",
        json={
            "question": "历史测试问题",
            "limit": 3,
        },
    )

    history_id = ask_response.json()["history_id"]

    response = client.get(
        "/history",
        params={"limit": 10},
    )

    assert response.status_code == 200

    data = response.json()
    matching_records = [
        record
        for record in data
        if record["id"] == history_id
    ]

    assert len(matching_records) == 1
    assert matching_records[0]["question"] == "历史测试问题"
    assert matching_records[0]["answer"] == "测试答案"
    assert matching_records[0]["sources"][0]["file_id"] == 27


def test_list_history_rejects_invalid_limit():
    response = client.get(
        "/history",
        params={"limit": 0},
    )

    assert response.status_code == 422

def test_search_includes_filename(monkeypatch):
    upload_response = client.post(
        "/upload",
        files={
            "file": (
                "source-name.txt",
                BytesIO(b"source content"),
                "text/plain",
            )
        },
    )
    file_id = upload_response.json()["id"]

    monkeypatch.setattr(
        "app.main.retrieve_chunks",
        lambda question, limit: [{
            "text": "测试来源",
            "file_id": file_id,
            "chunk_index": 0,
            "distance": 0.1,
        }],
    )

    response = client.post(
        "/search",
        json={
            "question": "测试问题",
            "limit": 3,
        },
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["filename"] == (
        "source-name.txt"
    )

def test_index_file_rejects_duplicate(monkeypatch):
    upload_response = client.post(
        "/upload",
        files={
            "file": (
                "duplicate-index.txt",
                BytesIO(b"document content"),
                "text/plain",
            )
        },
    )
    file_id = upload_response.json()["id"]

    call_count = 0

    def fake_index_document(file_id, file_path):
        nonlocal call_count
        call_count += 1
        return 1

    monkeypatch.setattr(
        "app.main.index_document",
        fake_index_document,
    )

    first_response = client.post(
        f"/files/{file_id}/index"
    )
    second_response = client.post(
        f"/files/{file_id}/index"
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "File is already indexed",
    }
    assert call_count == 1