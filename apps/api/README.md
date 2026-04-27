# API App

当前后端是 `Python + FastAPI` 服务，已从纯内存 MVP 扩展到可选 SQLite / Neon(Postgres) 持久化，并接入系统面试官与 SecondMe 分身面试官两类 provider。

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

- 已补多 provider 骨架：支持 `system -> doubao` 与 `avatar -> secondme_*` 的路由结构
- 已补 `1-10` 轮校验与设置页轮次透传约束
- 已补 SQLite / Postgres 持久化骨架，可落 interviewer / interviewer_profiles / sessions / messages / feedback / question_bank
- 已新增正式题库表与使用记录：`formal_question_bank` / `formal_question_usage`
- 面试主链路已切到“数据库唯一出题源”：首题和后续题都从数据库选择，不再依赖豆包或 SecondMe 实时生成问题
- 已支持通过数据库 `interviewer_profiles` 维护第三方应用内的面试官 skill 与目标分身 `sk-...`
- 已补隐藏管理台 `/admin/interviewers`，可通过页面维护面试官资料、类型、skill 文本、访问 key 和专属题库
- 已补通用兜底题库管理入口：当面试官专属题库不足时，运行时会自动从全局题库补题
- 已补隐藏问卷 `/interviewer-questionnaire`：支持面试官姓名、稳定用户名、专属题库文本录入，并按用户名生成稳定 `interviewer_id`
- 问卷不再自动生成面试官专属题库，初版由面试官自己上传或粘贴专业题
- 已修复 SecondMe 实时通道 prompt 回显问题，避免内部 prompt 被误展示为面试题
- 已补真实页面路由：`/`、`/setup`、`/interview`、`/feedback`
- 通过内存仓储保存 session / messages / feedback
- 暴露前端已使用的 4 个核心接口
- SecondMe 调用逻辑拆分为 client / realtime / orchestration / feedback service

## 当前与下一阶段边界

- 当前代码仍保留旧的 SecondMe 接口链路作为 fallback
- 当前已补 `Visitor Chat` 与豆包的代码骨架，但尚未用真实凭证完成外部联调
- 当前数据库为“可选持久化”，只有配置 `DATABASE_URL` 后才会启用 SQLite 或 Neon/Postgres 落库
- 当前反馈页前端已展示总结、建议和每轮复盘，但 `dimensions` 与 `suggestedAnswer` 尚未完整透出
- 当前数据库出题策略已经收敛为轻量 MVP：通用开场题 + 专业题库 + 通用收尾题

下一阶段计划：

- 用真实凭证完成 `system interviewer -> 豆包` 联调
- 用真实凭证完成 `avatar interviewer -> SecondMe Visitor Chat` 联调
- 验证 SQLite / Neon 持久化、面试官 skill 入库与数据库题库维护策略
- 视情况再升级到更正式的数据库方案

## 本地运行

1. 进入目录并创建环境变量文件：

```bash
cd apps/api
cp .env.example .env
```

2. 在 `.env` 中填写：

当前本地跑通最少需要：

- `SECONDME_API_KEY` 与 `SECONDME_AVATAR_SHARE_CODE`
  如果你继续走当前 legacy SecondMe 链路
- `SECONDME_BASE_URL` 默认已指向当前可联调的预发环境，如需切回生产可手动覆盖
- `SECONDME_WS_ORIGIN` 默认使用 `https://second-me.cn`，用于兼容当前 websocket 网关握手
- `BACKEND_CORS_ORIGINS` 默认允许本地 Vite 开发地址访问 API
- `BACKEND_CORS_ORIGIN_REGEX` 默认允许 `localhost` / `127.0.0.1` 的任意本地端口，避免 Vite 自动切端口时报跨域
- `DATABASE_URL`
  仅当你希望启用持久化时再填写，例如：
  - `sqlite:///./interview-hub.sqlite3`
  - `postgresql://USER:PASSWORD@HOST:5432/neondb?sslmode=require`
  - `jdbc:postgresql://HOST:5432/neondb?user=USER&password=PASSWORD&sslmode=require`

下一阶段联调时将额外需要这些变量：

- `SECONDME_VISITOR_BASE_URL`
- `SECONDME_APP_CLIENT_ID`
- `SECONDME_APP_CLIENT_SECRET`
- `SECONDME_AVATAR_API_KEY`
  测试期先填写你在 SecondMe 侧手动生成的目标分身 `sk-...`；不要提交到 Git
  如果误填到旧变量 `SECONDME_API_KEY`，当前后端会临时兼容读取，但建议尽快复制到 `SECONDME_AVATAR_API_KEY`
- `SECONDME_OAUTH_AUTHORIZE_URL`
  官方 OAuth 授权页地址是 `https://go.second-me.cn/oauth/`
- `SECONDME_OAUTH_TOKEN_URL`
  官方授权码换 token 地址是 `https://api.mindverse.com/gate/lab/api/oauth/token/code`
- `SECONDME_OAUTH_REDIRECT_URI`
  本地建议使用 `http://localhost:8000/api/auth/secondme/callback`，并且必须和 SecondMe 控制台重定向 URI 完全一致；当前也兼容 `http://localhost:8000/api/auth/callback`
- `SECONDME_OAUTH_SCOPES`
  仅在调试 OAuth inspect 或后续做“用户授权绑定分身”时需要；当前手动 key 测试期不依赖该流程
- `SYSTEM_INTERVIEWER_ID`
- `SYSTEM_INTERVIEWER_NAME`
- `SYSTEM_INTERVIEWER_TITLE`
- `SYSTEM_INTERVIEWER_DESCRIPTION`
- `SYSTEM_INTERVIEWER_AVATAR_URL`
- `DOUBAO_API_KEY`
- `DOUBAO_MODEL`
- `DOUBAO_BASE_URL`
- `DOUBAO_REQUEST_TIMEOUT_SECONDS`
  豆包推理模型首包可能较慢，本地联调建议先设为 `90`
- `DOUBAO_MAX_RETRIES`
  豆包网络异常或 5xx/429 时的自动重试次数，本地联调建议先设为 `2`

说明：

- `Visitor Chat`、豆包、SQLite、Postgres 的代码入口已经补上
- 当前 Visitor Chat 联调主路径是：后端用 `SECONDME_APP_CLIENT_ID / SECRET` 换 app token，再用 `SECONDME_AVATAR_API_KEY` 访问目标分身
- `GET /api/auth/secondme/login?inspect=true` 可用于检查 SecondMe OAuth 登录后返回了哪些字段；该检查不会打印真实 token 或 sk
- `GET /api/auth/secondme/login` 仍保留为后续“用户授权绑定自己的分身”实验入口；当前 MVP 面试主流程不依赖它
- 但在开始真实联调前，你仍然不需要先给生产凭证；更稳妥的做法是先提供测试环境凭证
- 如果没有 `SECONDME_APP_CLIENT_ID / SECRET`，avatar 面试官会继续回退到 legacy SecondMe provider
- 如果已经接入 Visitor Chat，但想支持多个分身或配置应用内 skill，优先使用隐藏管理台 `/admin/interviewers` 维护 `interviewer_profiles`

## 隐藏面试官管理台

前后端启动后，访问：

- `http://localhost:5173/admin/interviewers`

当前管理台能力：

- 查看当前系统面试官和 AI 分身面试官
- 新增、编辑、删除数据库中的面试官 profile
- 配置面试官类型、provider、名称、描述、头像、标签、支持岗位和支持模式
- 直接输入 skill 文本，或上传 `.txt` / `.md` 文件导入 skill
- 写入 SecondMe 目标分身 `sk-...`，页面只显示脱敏结果，不回显完整 key
- 维护“面试官专属题库”，推荐直接录专业八股题，格式为 `题目 | 参考答案 | 标签`
- 阶段支持直接写中文，如：`背景介绍`、`基础能力`、`项目深挖`、`系统设计`、`行为追问`、`总结收口`
- 单独维护“通用兜底题库”，不会被某个面试官的编辑覆盖
- 支持按岗位读取和保存通用题库：`GET/PUT /api/v1/admin/question-bank/global`

注意：

- 这是内测隐藏页面，不在主导航展示
- 当前还没有正式管理鉴权；部署到公网前必须补管理密码、后台登录或其他权限保护
- 保存能力依赖 `DATABASE_URL`，没有数据库时只能查看默认配置，不能持久化修改

## 面试官 Skill 数据库录入兜底

配置 `DATABASE_URL` 并重启后端后，后端会自动创建 `interviewer_profiles` 表。通常建议使用隐藏管理台录入；如果页面不可用，测试阶段也可以在 DBeaver 里手动维护这张表：

```sql
INSERT INTO interviewer_profiles (
  interviewer_id,
  skill_prompt,
  avatar_api_key,
  enabled,
  created_at,
  updated_at
)
VALUES (
  'secondme_tech',
  $$这里填写你的面试官 skill 文本$$,
  'sk-这里填写目标分身 API Key',
  TRUE,
  NOW()::text,
  NOW()::text
)
ON CONFLICT (interviewer_id) DO UPDATE SET
  skill_prompt = excluded.skill_prompt,
  avatar_api_key = excluded.avatar_api_key,
  enabled = excluded.enabled,
  updated_at = NOW()::text;
```

说明：

- `interviewer_id` 需要和当前面试官配置一致，例如默认 AI 分身面试官是 `secondme_tech`
- `skill_prompt` 是 Interview Hub 自己传给模型的面试官规则，会优先拼进系统面试官或 AI 分身面试官 prompt
- `avatar_api_key` 是访问目标 SecondMe 分身的 `sk-...`；如果这一列为空，后端会继续回退到 `interviewer_secrets`，再回退到 `.env` 的 `SECONDME_AVATAR_API_KEY`
- `interviewers` 表是 catalog 同步表，不建议手动改；手动维护请优先使用 `interviewer_profiles`
- 如果通过问卷创建面试官，默认 `interviewer_id` 形如 `questionnaire_<role>_<username>`

## 数据库出题规则

- 当前运行时不再调用豆包或 SecondMe 来“生成下一题”
- 当前初版采用更轻的固定流程：
  - 第一题走通用开场题
  - 中间轮次统一走“专业题库 / 八股题”
  - 最后一题走通用收尾题（当总轮次大于等于 3 时）
- 选题顺序固定为：
  - 开场题和收尾题优先走全局通用题库
  - 中间专业题先查当前面试官自己的 `formal_question_bank`
  - 若专业题不足，再查同岗位的全局 `formal_question_bank(scope=global)`
- 同一场面试内不会重复使用同一题；实际使用记录会写入 `formal_question_usage`
- provider 仍然保留，但当前主要用于反馈生成或后续扩展，不再作为出题来源
- 默认后端通用八股题库已扩展为 6 组 60 题：Java/语言基础、MySQL、Redis、计算机网络与系统、分布式与微服务、算法与数据结构
- 默认 `secondme_tech` 也带有 3 道示例专属题，用于验证“面试官专属题库优先、通用题库兜底”的运行逻辑
- 初版推荐的运营方式是：
  - 通用题库维护固定开场题和固定收尾题
  - 面试官专属题库只维护专业题，不要求细分复杂阶段

## 管理接口

- `GET /api/v1/admin/interviewers`
  - 读取系统面试官和数据库面试官
- `POST /api/v1/admin/interviewers`
  - 新增或按 `id` 覆盖面试官 profile
- `PUT /api/v1/admin/interviewers/{interviewer_id}`
  - 更新指定面试官
- `DELETE /api/v1/admin/interviewers/{interviewer_id}`
  - 删除指定面试官
- `GET /api/v1/admin/question-bank/global?role=<role>`
  - 读取指定岗位的通用题库
- `PUT /api/v1/admin/question-bank/global`
  - 覆盖指定岗位的通用题库

3. 安装依赖并运行：

```bash
python -m pip install --upgrade pip
pip install .
uvicorn app.main:app --reload
```

默认服务地址：

- `http://127.0.0.1:8000`

## 说明

- 当前版本默认仍以内存运行时为主；只有配置 `DATABASE_URL` 时才会启用 SQLite / Postgres 持久化
- 即使开启 SQLite / Postgres，SecondMe / Visitor Chat 的运行时连接仍然是进程内状态，服务重启后不能续接正在进行中的会话
- 当前反馈为本地启发式生成，后续可替换成真实模型评估
- `docs/openapi.yaml` 与 `openspec/` 仍然是前后端共享规范来源
- 当前本地默认使用 SecondMe 预发环境，因为这台机器无法解析生产域名 `mindos.mindverse.ai`
- 当前实时连接使用 `websocket-client` 适配预发 websocket 网关，保留原有异步服务接口
- 前端默认可以通过 `http://127.0.0.1:5173` 或 `http://localhost:5173` 直接调用这个后端
- 如果后续切到 Visitor Chat 匿名模式，终端用户不需要登录 SecondMe，但后端需要先通过开发者应用身份换取 app token
- 当前 question bank 仍是 MVP 入库形态，已支持通用题沉淀，但尚未接入题目复用/检索策略
- 当前 question bank 已拆成两层：
  - `question_bank`：历史留痕/兼容旧逻辑
  - `formal_question_bank`：正式运行时题库
- 当前后端会优先从数据库 `interviewer_profiles` 表读取 `avatar_api_key`；如果查不到，会回退到 `interviewer_secrets`，最后回退到 `SECONDME_AVATAR_API_KEY`
- 当前 OAuth 同步不是主流程：真实检查显示 OAuth token 与 user/info 不直接返回 `sk-...`，后续若要自动绑定用户分身，需要平台侧生成/查询 avatar key 的正式接口与权限
- 隐藏管理台已补齐基础 CRUD；后续需要补正式鉴权、批量导入、测试 key / 生产 key 区分和操作审计
- 当前实时通道会过滤发给分身的内部 prompt 和回显片段，避免 prompt 泄漏到 `/api/v1/interview-sessions` 的题目内容里
