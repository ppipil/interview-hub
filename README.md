# Interview Hub

AI 模拟面试 MVP 的 monorepo 根目录。

## Workspace Layout

- `apps/web`
  - Vite + React + TypeScript 前端
- `apps/api`
  - FastAPI 后端，当前已接入 SecondMe MVP 面试链路
- `docs`
  - `PRD.md`、`design.md`、`openapi.yaml`
- `openspec`
  - 需求变更与实现规范
- `stitch_exports`
  - 只读视觉草图资产

## Commands

- 根目录启动前端：`npm run dev`
- 根目录构建前端：`npm run build`
- 单独运行 web：`npm run dev --workspace @interview-hub/web`
- 单独运行 API：`cd apps/api && uvicorn app.main:app --reload`

## Current Status

- 前端主流程已具备：首页、设置页、面试页、反馈页
- 后端当前是 FastAPI + SecondMe 的 MVP 方案，本地链路可跑通
- 设置页已支持 `1-10` 轮选择，默认 `3` 轮
- 后端已补多面试官 provider 骨架，包含 `system -> doubao` 与 `avatar -> secondme_*`
- 当前已支持可选 SQLite / Neon(Postgres) 持久化骨架，可落 interviewer / interviewer_profiles / sessions / messages / feedback / question_bank
- AI 分身面试官已支持先在数据库中维护应用内 `skill_prompt` 与目标分身 `sk-...`
- 已补隐藏管理台 `/admin/interviewers`，可录入/编辑/删除面试官资料、类型、skill 和访问 key
- 当前 SecondMe 仍保留 legacy 链路作为兜底；`Visitor Chat` 代码路径已接入，测试期先使用手动生成的目标分身 `sk-...`

## Planned Next Work

- 用测试凭证完成豆包真实联调
- 用手动生成的目标分身 `sk-...` 完成 SecondMe `Visitor Chat` 真实联调
- 为隐藏管理台补管理权限保护、批量导入和更正式的线上运维流程
- 验证 SQLite / Neon(Postgres) 持久化与 question bank 入库策略
- 视情况升级到更正式的数据库与部署方案

## SecondMe Note

- 当前代码仍使用旧的 SecondMe 认证与聊天链路
- 目标方案是迁移到 `Visitor Chat`
- 测试期使用项目方手动生成的目标分身 `sk-...`，配置在后端 `.env` 的 `SECONDME_AVATAR_API_KEY`
- 在目标方案里，终端用户不需要登录 SecondMe；后端使用开发者应用身份换取 app token，并携带目标分身 key 访问 Visitor Chat
- OAuth inspect 仅用于排查 SecondMe 登录返回字段，不作为当前 MVP 面试主流程依赖
- 详细后端运行说明见 [apps/api/README.md](/Users/pipilu/Documents/Projects/interview-hub/apps/api/README.md)

## Notes

- 当前前端应用已迁移到 [apps/web](/Users/pipilu/Documents/Projects/interview-hub/apps/web)
- 后续新增需求默认先更新 `OpenSpec`，再改代码
- 本轮工作计划已记录在 [expand-interviewer-providers-and-question-bank](/Users/pipilu/Documents/Projects/interview-hub/openspec/changes/expand-interviewer-providers-and-question-bank/proposal.md)
