📄 PRD（Codex执行版）
项目名称

AI 面试练习（SecondMe版）

一、产品目标（必须明确）

构建一个最小可用产品，让用户可以：

选择岗位 + 模式 + 面试官（支持SecondMe分身）
完成一轮模拟面试（1-3个问题）
获得可读的反馈结果

👉 MVP只验证一件事：

用户是否愿意用AI分身练面试

二、范围（必须做 vs 不做）
✅ 本版本必须实现
岗位选择（5个固定）
模式选择（2种）
面试官选择（系统 + SecondMe）
面试流程（提问 → 回答 → 追问1轮）
结果反馈（总结 + 3条建议）
❌ 本版本不做
用户系统（先用localStorage）
课程系统
复杂评分算法
成长曲线
marketplace
多轮复杂面试
三、核心流程（最重要）
首页 → 设置 → 面试 → 结果 → 再来一次
四、页面定义（直接对应前端）
1️⃣ 首页
UI元素
标题：AI面试练习
按钮：开始练习
行为

点击按钮 → 跳转 /setup

2️⃣ 设置页（核心）
数据结构
{
  "role": "frontend",
  "mode": "guided",
  "interviewer": "system_tech"
}
UI结构
模块1：岗位选择
前端工程师
后端工程师
产品经理
运营
数据
模块2：模式
引导模式（guided）
真实模式（real）
模块3：面试官

分两组：

系统面试官

技术面试官 (system_tech)
HR (system_hr)

SecondMe分身

avatar_1
avatar_2

（先写死2个）

行为

点击「开始面试」

→ POST /api/start

3️⃣ 面试页
状态结构
{
  "question": "介绍一下你的项目",
  "step": 1,
  "history": []
}
UI
面试官头像 + 名字
问题
输入框
按钮：
提交
跳过
行为
Step 1

POST /api/answer

{
  "answer": "...",
  "step": 1
}

返回：

{
  "next_question": "为什么这么设计？",
  "step": 2
}
Step 2（最多2轮）

再答一次 → 结束

→ 跳转 /result

4️⃣ 结果页
数据结构
{
  "summary": "整体表达清晰，但深度不足",
  "improvements": [
    "增加技术细节",
    "减少空话",
    "结构更清晰"
  ],
  "better_answer": "示例优化回答..."
}
UI
总结
3条建议
优化答案
按钮：再练一次
五、API设计（后端最小）
1️⃣ 开始面试

POST /api/start

输入：

{
  "role": "frontend",
  "mode": "guided",
  "interviewer": "system_tech"
}

输出：

{
  "question": "介绍一下你的项目"
}
2️⃣ 回答问题

POST /api/answer

输入：

{
  "answer": "...",
  "step": 1
}

输出：

{
  "next_question": "为什么这么设计？"
}
3️⃣ 获取反馈

POST /api/result

输入：

{
  "conversation": [...]
}

输出：

{
  "summary": "...",
  "improvements": [...],
  "better_answer": "..."
}
六、AI逻辑（可以直接写prompt）
🎯 start prompt
你是一个{岗位}面试官，现在进行面试。
请提出第一个问题。
🎯 follow-up prompt
根据用户回答，提出一个追问问题。
要求更深入。
🎯 feedback prompt
根据以下面试对话：

1. 给出总体评价（1句话）
2. 给出3条具体改进建议
3. 给出一个更好的示例回答
七、SecondMe接入（MVP版本）
做法（简单版）

interviewer字段：

system_tech
system_hr
avatar_xxx
逻辑

如果是：

system → 用默认prompt
avatar → 加一句：
你正在扮演一个{人设描述}的面试官

👉 就够了（不要做复杂）

八、技术建议（给你省时间）

前端：

React + Vite（最快）

后端：

Python

AI：

直接调用 API
九、完成标准（Definition of Done）

上线版本必须：

能走完整流程（设置 → 面试 → 反馈）
无报错
每次都有结果输出