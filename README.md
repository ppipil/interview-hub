# Interview Hub

AI 模拟面试 MVP 的仓库根目录。

## Workspace Layout

- `apps/web`
  - Vite + React + TypeScript 前端壳子
- `apps/api`
  - 预留给未来 Python / Node.js 后端
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

## Notes

- 当前前端应用已迁移到 [apps/web](/Users/pipilu/Documents/Projects/interview-hub/apps/web)
- 后续新增需求默认先更新 `OpenSpec`，再改代码
