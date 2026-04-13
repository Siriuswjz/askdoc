# 企业文档问答系统

基于 RAG（检索增强生成）技术的企业内部文档智能问答平台。上传公司文档后，用自然语言提问，AI 直接从文档中找到答案并标注来源。

---

## 功能特性

- **多格式文档支持**：PDF、Word（.docx）、TXT
- **智能问答**：基于文档内容回答，不会凭空编造
- **引用溯源**：每条回答标注来自哪个文档、哪一页
- **多文档检索**：可跨多个文档同时检索，也可指定特定文档查询
- **迭代检索**：Claude 在回答不确定时会自动追加搜索，获取更多上下文

---

## 技术栈

| 层次 | 技术 |
|------|------|
| API 框架 | FastAPI + uvicorn |
| 向量数据库 | PostgreSQL + pgvector |
| 嵌入模型 | sentence-transformers（`all-MiniLM-L6-v2`，本地运行） |
| 大语言模型 | Claude Opus 4.6（Anthropic API） |
| ORM | SQLAlchemy 2.0（异步） |
| PDF 解析 | pdfplumber |
| Word 解析 | python-docx |

---

## 项目结构

```
RAG/
├── app/
│   ├── main.py                    # FastAPI 应用入口，启动时自动初始化数据库
│   ├── config.py                  # 配置管理（读取 .env）
│   ├── database.py                # 数据库连接、pgvector 扩展初始化
│   ├── models.py                  # 数据库模型（Document、DocumentChunk）
│   ├── schemas.py                 # 请求/响应数据结构
│   ├── api/
│   │   ├── documents.py           # 文档上传、查询、删除接口
│   │   └── qa.py                  # 问答接口
│   └── services/
│       ├── document_processor.py  # 文档解析 + 文本分块
│       ├── embedding_service.py   # 文本向量化（sentence-transformers）
│       ├── retrieval_service.py   # pgvector 相似度检索
│       └── llm_service.py         # Claude API 调用 + Tool Calling 循环
├── docker-compose.yml             # PostgreSQL 16 + pgvector 容器
├── requirements.txt               # Python 依赖
├── .env.example                   # 环境变量模板
└── .env                           # 本地配置（需自行填写，不提交 git）
```

---

## 快速开始

### 1. 环境准备

**前置条件：**
- Python 3.11+
- Docker（用于运行 PostgreSQL）
- Anthropic API Key（[获取地址](https://console.anthropic.com/)）

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖（首次安装较慢，需下载 PyTorch 和嵌入模型）
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 API Key：

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx   # 必填
DATABASE_URL=postgresql+asyncpg://raguser:ragpassword@localhost:5432/ragdb
UPLOAD_DIR=./uploads
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=800
CHUNK_OVERLAP=100
RETRIEVAL_TOP_K=5
```

### 4. 启动数据库

```bash
docker compose up -d
```

### 5. 启动服务

```bash
uvicorn app.main:app --reload --port 8000
```

服务启动后访问：
- **API 文档（交互式）**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health

---

## API 使用说明

### 上传文档

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@员工手册.pdf"
```

**响应示例：**
```json
{
  "id": "d3f1a2b4-...",
  "original_filename": "员工手册.pdf",
  "file_type": "pdf",
  "total_chunks": 42,
  "created_at": "2026-04-05T10:00:00"
}
```

### 查询文档列表

```bash
curl http://localhost:8000/api/documents/
```

### 删除文档

```bash
curl -X DELETE http://localhost:8000/api/documents/{document_id}
```

### 提问

```bash
curl -X POST http://localhost:8000/api/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "年假有几天？"}'
```

**响应示例：**
```json
{
  "answer": "根据员工手册第3章，正式员工每年享有10天带薪年假。工作满5年后增加至15天。",
  "sources": [
    {
      "document_id": "d3f1a2b4-...",
      "filename": "员工手册.pdf",
      "chunk_index": 12,
      "page_number": 8,
      "content_preview": "第三章 假期制度\n3.1 年假..."
    }
  ]
}
```

### 在指定文档中提问

```bash
curl -X POST http://localhost:8000/api/qa/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "违约金条款是什么？",
    "document_ids": ["d3f1a2b4-...", "e5c2b1a3-..."]
  }'
```

---

## RAG 工作流程

```
用户提问
   ↓
向量化问题（all-MiniLM-L6-v2）
   ↓
pgvector 余弦相似度检索 Top-K 文档片段
   ↓
将片段 + 问题发送给 Claude Opus 4.6
   ↓
Claude 生成回答
（若信息不足，自动调用 search_documents 工具追加检索）
   ↓
返回答案 + 引用来源
```

---

## 配置说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `CHUNK_SIZE` | 800 | 文本分块大小（字符数） |
| `CHUNK_OVERLAP` | 100 | 相邻块的重叠字符数，避免截断关键信息 |
| `RETRIEVAL_TOP_K` | 5 | 每次检索返回的最相关片段数量 |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | 嵌入模型，首次运行自动下载（约 90MB） |

---

## 注意事项

- 首次启动时嵌入模型会自动从 HuggingFace 下载，需要网络连接
- `.env` 文件包含密钥，不要提交到 Git（已在 `.gitignore` 中排除）
- 删除文档时，对应的所有向量数据会级联删除
- 问答质量取决于文档内容质量和分块策略，可根据实际情况调整 `CHUNK_SIZE`
