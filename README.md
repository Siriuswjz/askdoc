# DocMind — 企业文档问答系统

基于 RAG（检索增强生成）技术的企业内部文档智能问答平台。上传公司文档后，用自然语言提问，AI 直接从文档中找到答案并标注来源。

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green) ![pgvector](https://img.shields.io/badge/pgvector-PostgreSQL-blue)

---

## 功能特性

- **多格式文档支持**：PDF、Word（.docx）、TXT
- **两阶段检索 + Rerank**：向量召回 20 个候选，再由 BGE-Reranker 交叉编码精选 Top-5，显著降低"答非所问"概率
- **多轮对话**：上下文连续追问，"刚才那份合同的第三条是什么意思？"也能答对
- **智能问答**：基于文档内容回答并附带引用来源，不会凭空编造
- **多文档检索**：可跨多个文档检索，也可圈定特定文档查询
- **内置 Web UI**：无需单独部署前端

---

## 技术栈

| 层次 | 技术 |
|------|------|
| API 框架 | FastAPI + Uvicorn |
| 向量数据库 | PostgreSQL 16 + pgvector |
| 嵌入模型 | `BAAI/bge-large-zh-v1.5`（硅基流动） |
| 重排序模型 | `BAAI/bge-reranker-v2-m3`（硅基流动） |
| 大语言模型 | `DeepSeek-R1-Distill-Qwen-7B`（硅基流动） |
| ORM | SQLAlchemy 2.0（异步） |

---

## RAG 工作流程

```
上传文档 → 解析分块 → 向量化（BGE-large） → 存入 pgvector
                                                      ↓
用户提问 → 向量化 → 余弦相似度召回 Top-20
                          ↓
               BGE-Reranker 精选 Top-5
                          ↓
          拼接对话历史 + 上下文 → DeepSeek LLM → 答案 + 来源引用
```

---

## 快速开始（本地开发）

### 1. 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

复制模板并填入 API Key：

```bash
cp .env.example .env
```

```env
SILICONFLOW_API_KEY=your_api_key   # 必填，在 siliconflow.cn 注册后获取
```

其余参数保持默认即可。

### 3. 启动数据库

```bash
docker compose up postgres -d
```

### 4. 启动服务

```bash
uvicorn app.main:app --reload --port 8000
```

访问 http://localhost:8000 打开 Web 界面。

---

## 一键 Docker 部署（本地全栈）

```bash
docker compose up --build
```

同时启动 PostgreSQL 和应用，访问 http://localhost:8000。

---

## 公网部署（Railway）

> 部署完成后获得公网域名，面试演示直接打开即可。

1. 在 [railway.app](https://railway.app) 新建项目，Add Plugin → **PostgreSQL**（已内置 pgvector）
2. 连接 GitHub 仓库，Railway 自动识别 `railway.toml` 并构建
3. 在 Variables 面板添加 `SILICONFLOW_API_KEY`
4. `DATABASE_URL` 使用 Railway 自动注入的值，无需修改（格式自动兼容）
5. Deploy → 获得 `xxx.railway.app` 域名

---

## 配置说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `SILICONFLOW_API_KEY` | — | 必填 |
| `RETRIEVAL_TOP_K` | 5 | 最终送入 LLM 的片段数 |
| `RETRIEVAL_CANDIDATES` | 20 | Reranker 前的候选召回数 |
| `USE_RERANK` | true | 关闭可降级为纯向量检索 |
| `CONVERSATION_HISTORY_LIMIT` | 10 | 多轮对话传给 LLM 的最大历史条数 |
| `CHUNK_SIZE` | 800 | 文本分块大小（字符数） |
| `CHUNK_OVERLAP` | 100 | 相邻块重叠字符数 |
