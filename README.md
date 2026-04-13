# DocMind — 企业文档问答系统

基于 RAG（检索增强生成）技术的企业内部文档智能问答平台。上传公司文档后，用自然语言提问，AI 直接从文档中找到答案并标注来源。

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green) ![pgvector](https://img.shields.io/badge/pgvector-PostgreSQL-blue)

---

## 功能特性

- **多格式文档支持**：PDF、Word（.docx）、TXT
- **智能问答**：基于文档内容回答，不会凭空编造，答案附带引用来源
- **可视化界面**：内置 Web UI，无需额外部署前端
- **多文档检索**：可跨多个文档同时检索，也可指定特定文档查询

---

## 技术栈

| 层次 | 技术 |
|------|------|
| API 框架 | FastAPI + uvicorn |
| 向量数据库 | PostgreSQL + pgvector |
| 嵌入模型 | `BAAI/bge-large-zh-v1.5`（硅基流动 API） |
| 大语言模型 | DeepSeek-R1-Distill-Qwen-7B（硅基流动 API） |
| ORM | SQLAlchemy 2.0（异步） |

---

## 快速开始

### 1. 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

新建 `.env` 文件：

```env
SILICONFLOW_API_KEY=your_api_key   # 硅基流动 API Key，必填
DATABASE_URL=postgresql+asyncpg://raguser:ragpassword@localhost:5432/ragdb
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
CHUNK_SIZE=800
CHUNK_OVERLAP=100
RETRIEVAL_TOP_K=5
```

硅基流动 API Key 在 [siliconflow.cn](https://siliconflow.cn) 注册后获取。

### 3. 启动数据库

需要 Docker，启动 PostgreSQL 16 + pgvector：

```bash
docker compose up -d
```

### 4. 启动服务

```bash
uvicorn app.main:app --reload --port 8000
```

访问 http://localhost:8000 打开 Web 界面。

---

## RAG 工作流程

```
上传文档 → 解析分块 → 向量化 → 存入 pgvector
                                        ↓
用户提问 → 向量化问题 → 余弦相似度检索 Top-K 片段 → 发给 LLM → 返回答案 + 来源
```

---

## 配置说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `CHUNK_SIZE` | 800 | 文本分块大小（字符数） |
| `CHUNK_OVERLAP` | 100 | 相邻块重叠字符数，避免截断关键信息 |
| `RETRIEVAL_TOP_K` | 5 | 每次检索返回的最相关片段数 |
| `EMBEDDING_MODEL` | BAAI/bge-large-zh-v1.5 | 硅基流动 embedding 模型 |
