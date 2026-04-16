# API App

当前后端已按无数据库 MVP 方案初始化为 `Python + FastAPI` 骨架，并准备接入一个固定的 SecondMe 分身面试官。

## 目录结构

```text
apps/api
├── app
│   ├── api
│   ├── core
│   ├── models
│   ├── repositories
│   └── services
├── .env.example
└── pyproject.toml
```

## 当前能力

- 固定一个 SecondMe 面试官配置
- 通过内存仓储保存 session / messages / feedback
- 暴露前端已使用的 4 个核心接口
- SecondMe 调用逻辑拆分为 client / realtime / orchestration / feedback service

## 本地运行

1. 进入目录并创建环境变量文件：

```bash
cd apps/api
cp .env.example .env
```

2. 在 `.env` 中填写：

- `SECONDME_API_KEY`
- `SECONDME_AVATAR_SHARE_CODE`
- `SECONDME_BASE_URL` 默认已指向当前可联调的预发环境，如需切回生产可手动覆盖
- `SECONDME_WS_ORIGIN` 默认使用 `https://second-me.cn`，用于兼容当前 websocket 网关握手
- `BACKEND_CORS_ORIGINS` 默认允许本地 Vite 开发地址访问 API
- `BACKEND_CORS_ORIGIN_REGEX` 默认允许 `localhost` / `127.0.0.1` 的任意本地端口，避免 Vite 自动切端口时报跨域

3. 安装依赖并运行：

```bash
python -m pip install --upgrade pip
pip install .
uvicorn app.main:app --reload
```

默认服务地址：

- `http://127.0.0.1:8000`

## 说明

- 当前版本不接数据库，服务重启后会话会清空
- 当前反馈为本地启发式生成，后续可替换成真实模型评估
- `docs/openapi.yaml` 与 `openspec/` 仍然是前后端共享规范来源
- 当前本地默认使用 SecondMe 预发环境，因为这台机器无法解析生产域名 `mindos.mindverse.ai`
- 当前实时连接使用 `websocket-client` 适配预发 websocket 网关，保留原有异步服务接口
- 前端默认可以通过 `http://127.0.0.1:5173` 或 `http://localhost:5173` 直接调用这个后端
