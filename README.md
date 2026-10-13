# AI Doc Assistant

[![Tests](https://github.com/ppp110888/ai-doc-assistant/actions/workflows/tests.yml/badge.svg)](https://github.com/ppp110888/ai-doc-assistant/actions/workflows/tests.yml)

一个基于 FastAPI、DeepSeek 和 Chroma 构建的文档知识库问答后端。

系统支持上传 TXT、PDF 和 DOCX 文档，完成文本提取、清洗、切分、向量化和语义检索，并让大模型根据检索结果生成带来源的回答。

## 核心功能

- TXT、PDF、DOCX 文件上传
- 文件类型和大小校验
- SQLite 文件记录管理
- 文档文本提取与清洗
- 带重叠的文本切分
- 中文文本 embedding
- Chroma 向量持久化
- 语义检索与来源追踪
- DeepSeek RAG 问答
- 问答历史保存与查询
- 文件索引状态管理
- 重复索引保护
- 自动化测试

## 技术栈

- Python 3.11
- FastAPI
- SQLAlchemy
- SQLite
- Alembic
- DeepSeek API
- FastEmbed
- BAAI/bge-small-zh-v1.5
- Chroma
- Pytest

## 项目结构

```text
app/
├── main.py
├── database.py
├── models.py
└── services/
    ├── documents.py
    ├── embeddings.py
    ├── files.py
    ├── indexing.py
    ├── llm.py
    ├── rag.py
    ├── retrieval.py
    ├── sources.py
    ├── text_processing.py
    └── vector_store.py

migrations/
tests/
uploads/
chroma_db/
```

## 本地运行

### 1. 创建虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. 安装依赖

```powershell
python -m pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`，填写：

```env
DEEPSEEK_API_KEY=your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

不要把 `.env` 或真实 API Key 提交到 Git。

### 4. 执行数据库迁移

```powershell
python -m alembic upgrade head
```

### 5. 启动服务

```powershell
python -m uvicorn app.main:app --reload
```

访问 Swagger：

```text
http://127.0.0.1:8000/docs
```

## 使用流程

1. 调用 `POST /upload` 上传文档。
2. 记录响应中的文件 `id`。
3. 调用 `POST /files/{file_id}/index` 建立向量索引。
4. 调用 `POST /search` 查看语义检索结果。
5. 调用 `POST /ask` 进行知识库问答。
6. 调用 `GET /history` 查看问答历史。

## 主要接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| POST | `/upload` | 上传文档 |
| GET | `/files` | 文件列表 |
| GET | `/files/{file_id}` | 文件详情 |
| POST | `/files/{file_id}/index` | 建立文档索引 |
| POST | `/search` | 语义检索 |
| POST | `/ask` | RAG 知识库问答 |
| GET | `/history` | 问答历史 |
| POST | `/chat` | 普通大模型问答 |

## RAG 流程

```text
上传文档
-> 提取文本
-> 清洗与切分
-> 生成 512 维向量
-> 写入 Chroma
-> 问题向量化
-> Top-K 语义检索
-> 构造受资料约束的提示词
-> DeepSeek 生成回答
-> 返回答案和来源
```

## 自动化测试

```powershell
python -m pytest -q
```

当前测试覆盖：

- 文件上传与校验
- 文档解析
- 文本清洗与切分
- embedding 服务
- Chroma 存储和检索
- 文档索引
- RAG 服务
- API 错误处理
- 问答历史
- 索引状态和重复索引

## 当前限制

- 当前使用 SQLite，适合单机学习和演示
- 文本按字符长度切分，尚未按语义或 token 切分
- PDF 仅支持包含文本层的文件，不支持扫描件 OCR
- 暂未实现用户认证和多租户隔离
- 暂未部署到云端

## 后续计划

- 切换 PostgreSQL
- 增加检索相关性阈值
- 增加文档删除和重新索引
- 增加简单前端页面
- 建立 RAG 评估数据集

## Docker 运行

确保 Docker Desktop 已启动，并创建好 `.env`：

```powershell
docker compose up -d --build
```

查看容器状态：

```powershell
docker compose ps
```

查看日志：

```powershell
docker compose logs -f app
```

停止容器：

```powershell
docker compose down
```

SQLite、上传文件、Chroma 数据和 embedding 模型缓存均会持久化，重新启动容器不会丢失。

访问接口文档：

```text
http://127.0.0.1:8000/docs
```