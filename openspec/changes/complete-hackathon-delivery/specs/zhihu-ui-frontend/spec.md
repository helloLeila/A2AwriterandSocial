## ADDED Requirements

### Requirement: 话题启动区面板
用户 SHALL 在页面顶部看到一个话题启动区，包含知乎问题标题输入/展示、开始按钮、以及后台Agent状态提示。

#### Scenario: 输入知乎链接启动流程
- **WHEN** 用户在输入框粘贴知乎问题链接并点击「开始创作辅助」按钮
- **THEN** 系统调用 POST /api/session/start 创建会话
- **AND** 立即建立 WebSocket 连接 /ws/{session_id}
- **AND** 发送 {question_title: "..."} 作为首条WS消息
- **AND** 面板显示采集Agent和过滤Agent的实时状态（🔍采集中... → ✅采集完成）

#### Scenario: 预设问题快速体验
- **WHEN** 用户点击预设的热门知乎问题卡片
- **THEN** 系统自动填充该问题链接和标题
- **AND** 直接进入流程

### Requirement: A2A实时社交日志面板
系统 SHALL 以逐行动态滚动方式展示用户Agent与答主Agent的多轮对话，仅展示社交主体内容，标注时间戳和轮次。

#### Scenario: 多轮对话实时展示
- **WHEN** WebSocket 推送 chat_message 类型消息
- **THEN** 面板逐行追加显示对话内容
- **AND** 用户Agent消息使用左侧蓝色头像+气泡
- **AND** 答主Agent消息使用右侧绿色头像+气泡
- **AND** 每条消息标注时间戳和「第N轮」标签
- **AND** 对话区域自动滚动到底部

#### Scenario: 对话轮次状态指示
- **WHEN** 每轮对话开始/结束
- **THEN** 面板显示 round_start 和 round_end 状态提示
- **AND** 当前轮次数字高亮显示

### Requirement: 需求对齐看板面板
系统 SHALL 在对话完成后以可视化卡片形式展示 ConsensusBoard 内容。

#### Scenario: 共识看板展示
- **WHEN** WebSocket 推送 consensus_ready 消息
- **THEN** 面板切换到需求对齐看板
- **AND** 以4个卡片分别展示：用户核心需求、用户禁忌、答主创作方向、关键洞察
- **AND** 每个卡片使用图标+列表形式

### Requirement: 创作者辅助输出面板
系统 SHALL 仅展示写作框架（WriterFramework），绝对禁止展示完整回答正文。

#### Scenario: 写作框架展示
- **WHEN** WebSocket 推送 framework_ready 消息
- **THEN** 面板展示创作者辅助输出
- **AND** 包含：标题建议列表、切入角度列表、结构大纲（带层级）、避雷清单、语气指导
- **AND** 结构大纲使用可折叠层级展示
- **AND** 语气指导使用引用块样式突出

### Requirement: 知乎原生UI视觉风格
前端视觉 SHALL 1:1复刻知乎原生UI风格。

#### Scenario: 视觉风格验证
- **WHEN** 用户打开页面
- **THEN** 主色调使用知乎蓝 #0066FF
- **AND** 背景色使用知乎灰白 #F6F6F6
- **AND** 卡片使用白色背景+细边框+#EBEBEB阴影
- **AND** 字体使用 -apple-system, PingFang SC, Microsoft YaHei
- **AND** 按钮使用知乎蓝色圆角按钮风格
- **AND** 整体布局最大宽度 1000px 居中
