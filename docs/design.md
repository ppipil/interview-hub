🎨 核心设计系统 (Design System)
1. 色彩面板 (Color Palette)
不要使用刺眼的纯色，整体采用带有灰度的高级 SaaS 质感色彩，配合游戏化模块的马卡龙点缀色。

背景色 (Backgrounds)

全局底色：#F8FAFC (Tailwind: slate-50) - 提供微弱的冷灰底色，让纯白卡片能“浮”出来。

卡片底色：#FFFFFF (Tailwind: white) - 所有 Bento Box 和弹窗的默认背景。

主色调 (Primary Brand)

品牌蓝：#2563EB (Tailwind: blue-600) - 用于主按钮、选中状态。

渐变强调色：bg-gradient-to-r from-blue-600 to-indigo-600 - 用于最底部的“开始挑战”大按钮，增加游戏感。

模块语义色 (Semantic Colors)

带飞模式 (新手/引导)：#ECFDF5 (Tailwind: emerald-50) - 柔和的浅绿色背景。

地狱拉练 (高难/真实)：#FEF2F2 (Tailwind: red-50) - 柔和的浅红色背景。

文本色 (Typography Colors)

主要标题 (Primary Text)：#0F172A (Tailwind: slate-900) - 极深的蓝黑，避免死黑。

次要描述 (Secondary Text)：#64748B (Tailwind: slate-500) - 用于标签、提示语。

2. 排版层级 (Typography Hierarchy)
抛弃传统的“正规军”排版，采用更大胆、对比度更强的字体层级。

大标题 (Hero Title)：如“今天打算拿下哪个 Offer？” -> text-2xl font-extrabold tracking-tight (字号大、极粗、字间距微缩)。

模块标题 (Section Title)：如“翻牌你的面试官” -> text-lg font-bold text-slate-800。

正文/按钮文字 (Body & Button)：text-base font-medium。

性格标签 (Badges/Tags)：text-xs font-semibold tracking-wide。

3. 形状与圆角 (Shapes & Radii)
这是 Bento Box 风格的灵魂，拒绝直角，全面拥抱大圆角。

外层大卡片 (Bento 大区块)：rounded-3xl (极大的圆角，约 24px)。

内部小卡片 / 面试官卡片：rounded-2xl (大圆角，约 16px)。

操作按钮 / 标签 (Buttons & Chips)：rounded-full (全圆角/胶囊形)，强化可点击的暗示。

4. 阴影与立体感 (Elevation & Shadows)
不要用生硬的粗边框，用柔和的弥散阴影来制造页面的呼吸感。

默认悬浮卡片：shadow-[0_4px_20px_rgba(0,0,0,0.03)] (极其微弱、扩散面广的阴影)。

选中状态 (Active/Hover)：shadow-[0_8px_30px_rgba(37,99,235,0.12)] border border-blue-500 (带有一点主色调光晕的阴影，加上清晰的边界反馈)。

5. 间距系统 (Spacing & Grid)
页面全局边距：左右留白 px-6。

Bento Box 网格间距：卡片之间固定留白 gap-4 (约 16px)。

卡片内边距：p-6 (提供充足的呼吸空间，不让文字贴边)。
