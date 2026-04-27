# Interview Hub

一个用于 AI 模拟面试的 monorepo。当前版本已经打通了“配置面试 -> 实时答题 -> 反馈复盘”的主链路，并补上了隐藏管理台、面试官问卷、正式题库和多 provider 骨架。

## Workspace Layout

- `apps/web`
  - Vite + React + TypeScript + Zustand 前端
- `apps/api`
  - FastAPI 后端，负责 session、消息、反馈、题库和隐藏管理能力
- `docs`
  - PRD、设计稿说明、周报等项目文档
- `openspec`
  - 需求变更与实现规范
- `stitch_exports`
  - 只读视觉草图资产

## Current Routes

- `/`
  - 首页
- `/setup`
  - 面试配置页
- `/interview`
  - 面试页
- `/feedback`
  - 反馈页
- `/admin/interviewers`
  - 隐藏管理台，可维护面试官和通用题库
- `/interviewer-questionnaire`
  - 面试官快速录入问卷

前端路由现在已经和页面状态同步，不再出现首页、设置页、面试页、反馈页共用一个地址的情况。

## Quick Start

### Frontend

- 根目录启动前端：`npm run dev`
- 根目录构建前端：`npm run build`
- 单独运行 web：`npm run dev --workspace @interview-hub/web`

### API

- 启动后端：`cd apps/api && ./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`
- 运行后端测试：`cd apps/api && ./.venv/bin/python -m unittest discover -s tests`

详细后端配置说明见 [apps/api/README.md](/Users/pipilu/Documents/Projects/interview-hub/apps/api/README.md)。

## Current Product Status

- 主流程已完成：
  - 首页 -> 设置页 -> 面试页 -> 反馈页可完整跑通
- 面试配置已完成：
  - 固定 5 个岗位
  - `guided` / `real` 两种模式
  - `1-10` 轮配置，默认 `3` 轮
- 多面试官架构已落地：
  - `system -> doubao`
  - `avatar -> secondme_legacy / secondme_visitor`
- 后端题库已切到数据库唯一出题源：
  - 开场题和收尾题来自通用题库
  - 中间专业题优先使用面试官专属题库
  - 题库不足时自动回退到通用题库
- 隐藏管理能力已完成第一版：
  - 面试官 CRUD
  - skill / prompt / API key 维护
  - 面试官专属题库编辑
  - 通用题库按岗位读取与保存
- 面试官问卷已可用：
  - 支持录入面试官姓名
  - 支持稳定用户名，重复提交会更新同一位面试官
  - 支持绑定专属题库文本
- 反馈页已支持：
  - 总体总结
  - 改进建议
  - 每轮问题、候选人回答、评价、参考答案复盘
- Prompt 泄漏问题已处理：
  - `/api/v1/interview-sessions` 不再把发给 AI 分身的内部 prompt 直接展示给用户

## Question Bank Status

- 正式题库表：
  - `formal_question_bank`
  - `formal_question_usage`
- 当前后端默认题库已经按岗位和阶段入库
- 后端岗位默认“八股题库”已更新为 6 组 60 题：
  - Java / 语言基础
  - MySQL
  - Redis
  - 计算机网络与系统
  - 分布式与微服务
  - 算法与数据结构
- 问卷和管理台都支持使用文本格式维护题库：
  - `题目 | 参考答案 | 标签`
  - 或 `阶段 | 题目 | 参考答案 | 标签`

## Known Gaps

- 隐藏管理台还没有正式鉴权，不适合直接暴露公网
- 面试中的运行时连接和 session 仍是进程内状态，服务重启后不能续接
- 反馈页还没有把 `dimensions` 和 `suggestedAnswer` 全量展示出来
- 线上部署必须显式配置 `VITE_API_BASE_URL`
- 豆包与 SecondMe Visitor Chat 的真实联调仍依赖外部环境和测试凭证

## OpenSpec

- 后续新增需求默认先更新 `OpenSpec`，再改代码
- 当前这轮能力扩展主要记录在：
  - [expand-interviewer-providers-and-question-bank](/Users/pipilu/Documents/Projects/interview-hub/openspec/changes/expand-interviewer-providers-and-question-bank/proposal.md)
  - [add-interviewer-owned-question-banks](/Users/pipilu/Documents/Projects/interview-hub/openspec/changes/add-interviewer-owned-question-banks/proposal.md)
