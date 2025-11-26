# 需求文档

## 简介

AI 代理会议系统是一个允许用户配置多个 AI 代理（来自不同模型供应商）并让它们在虚拟会议中进行角色扮演讨论的应用程序。用户可以为每个代理设置角色，启动会议，观察代理之间的互动，并随时参与到讨论中。

## 术语表

- **AI Agent（AI 代理）**: 由特定 AI 模型驱动的虚拟参与者，具有指定的角色和行为模式
- **Meeting System（会议系统）**: 管理和协调 AI 代理讨论的核心应用程序
- **Model Provider（模型供应商）**: 提供 AI 模型服务的平台（如 OpenAI、Anthropic、Google 等）
- **Role（角色）**: 分配给 AI 代理的身份和行为指导，定义其在讨论中的立场和风格
- **Discussion Session（讨论会话）**: 一次完整的会议实例，包含多个代理的发言轮次
- **User Participant（用户参与者）**: 可以随时加入讨论的人类用户
- **Moderator（主持人）**: 负责组织会议进程、管理议题和引导讨论的参与者（可以是用户或 AI 代理）
- **Agenda（议题）**: 会议中需要讨论的具体话题或问题
- **Meeting Minutes（会议纪要）**: 对会议讨论内容的结构化总结，包含关键决策、结论和待办事项
- **Discussion Style（讨论风格）**: 定义会议氛围和交流方式的配置（如正式、轻松、辩论式）
- **Speaking Length Preference（发言长度偏好）**: 参与者发言详细程度的期望设置（简短、中等、详细）
- **Mention（提及）**: 使用 @ 符号引用特定参会者以请求其发言或回应的功能

## 需求

### 需求 1

**用户故事:** 作为用户，我想要配置多个 AI 代理，以便我可以创建具有不同观点和专业知识的虚拟会议参与者。

#### 验收标准

1. WHEN 用户创建新的 AI 代理 THEN Meeting System SHALL 允许用户指定模型供应商、模型名称、API 密钥和角色描述
2. WHEN 用户保存代理配置 THEN Meeting System SHALL 验证所有必需字段已填写并持久化配置
3. WHEN 用户查看已配置的代理列表 THEN Meeting System SHALL 显示所有代理及其关键信息（名称、角色、模型）
4. WHEN 用户编辑现有代理 THEN Meeting System SHALL 加载当前配置并允许修改所有字段
5. WHEN 用户删除代理 THEN Meeting System SHALL 移除该代理配置并更新代理列表

### 需求 2

**用户故事:** 作为用户，我想要支持多个模型供应商，以便我可以利用不同 AI 模型的独特能力和特点。

#### 验收标准

1. WHEN 用户选择模型供应商 THEN Meeting System SHALL 提供至少四个主流供应商选项（OpenAI、Anthropic、Google、GLM）
2. WHEN 用户为特定供应商配置 API 凭证 THEN Meeting System SHALL 安全存储凭证信息
3. WHEN Meeting System 调用 AI 模型 THEN Meeting System SHALL 使用适配器模式统一处理不同供应商的 API 接口
4. WHEN 模型 API 调用失败 THEN Meeting System SHALL 记录错误并向用户显示清晰的错误消息
5. WHEN 用户测试 API 连接 THEN Meeting System SHALL 发送测试请求并报告连接状态

### 需求 3

**用户故事:** 作为用户，我想要为每个 AI 代理设置角色，以便它们在讨论中表现出不同的观点和专业知识。

#### 验收标准

1. WHEN 用户定义代理角色 THEN Meeting System SHALL 接受包含角色名称、背景描述和行为指导的文本输入
2. WHEN 代理参与讨论 THEN Meeting System SHALL 将角色描述作为系统提示词发送给 AI 模型
3. WHEN 用户保存角色配置 THEN Meeting System SHALL 验证角色描述不为空且长度在合理范围内
4. WHEN 用户使用预设角色模板 THEN Meeting System SHALL 提供常见角色模板（如产品经理、工程师、设计师）供快速配置

### 需求 4

**用户故事:** 作为用户，我想要启动虚拟会议并观察 AI 代理讨论，以便我可以看到不同观点的碰撞和交流。

#### 验收标准

1. WHEN 用户启动新会议 THEN Meeting System SHALL 要求用户输入会议主题并选择参与的代理
2. WHEN 会议开始 THEN Meeting System SHALL 按照配置的顺序或随机顺序让代理依次发言
3. WHEN 代理发言 THEN Meeting System SHALL 将会议历史和当前上下文发送给对应的 AI 模型并获取响应
4. WHEN 代理完成发言 THEN Meeting System SHALL 将发言内容添加到会议记录并显示给用户
5. WHEN 所有代理完成一轮发言 THEN Meeting System SHALL 开始新一轮讨论或等待用户指令
6. WHEN 用户暂停会议 THEN Meeting System SHALL 停止代理发言并保持当前会议状态
7. WHEN 用户结束会议 THEN Meeting System SHALL 保存完整的会议记录并释放资源

### 需求 5

**用户故事:** 作为用户，我想要随时参与到 AI 代理的讨论中，以便我可以引导对话方向或提出问题。

#### 验收标准

1. WHEN 用户在会议进行中输入消息 THEN Meeting System SHALL 将用户消息插入到会议记录中
2. WHEN 用户发言后 THEN Meeting System SHALL 将用户消息作为上下文提供给后续发言的代理
3. WHEN 用户请求特定代理回应 THEN Meeting System SHALL 允许用户指定下一个发言的代理
4. WHEN 用户输入空消息 THEN Meeting System SHALL 拒绝提交并保持当前会议状态

### 需求 6

**用户故事:** 作为用户，我想要查看和管理会议历史，以便我可以回顾之前的讨论内容。

#### 验收标准

1. WHEN 会议进行中 THEN Meeting System SHALL 实时显示所有发言内容，包括发言者身份和时间戳
2. WHEN 用户查看历史会议 THEN Meeting System SHALL 显示所有已保存的会议列表及其基本信息
3. WHEN 用户打开历史会议 THEN Meeting System SHALL 加载并显示完整的会议记录
4. WHEN 用户导出会议记录 THEN Meeting System SHALL 提供文本格式（如 Markdown 或 JSON）的导出功能
5. WHEN 用户删除历史会议 THEN Meeting System SHALL 移除会议记录并更新会议列表

### 需求 7

**用户故事:** 作为用户，我想要控制会议的进行方式，以便我可以根据需要调整讨论的节奏和结构。

#### 验收标准

1. WHEN 用户配置会议设置 THEN Meeting System SHALL 允许用户设置发言轮次限制、每次发言的最大长度和发言顺序模式
2. WHEN 达到轮次限制 THEN Meeting System SHALL 自动结束会议并通知用户
3. WHEN 代理响应超过长度限制 THEN Meeting System SHALL 截断响应并在会议记录中标注
4. WHEN 用户选择随机发言顺序 THEN Meeting System SHALL 在每轮随机选择下一个发言的代理
5. WHEN 用户选择轮流发言顺序 THEN Meeting System SHALL 按照代理列表顺序依次让代理发言

### 需求 8

**用户故事:** 作为开发者，我想要系统具有清晰的架构和可扩展性，以便未来可以轻松添加新功能和支持更多模型供应商。

#### 验收标准

1. WHEN 添加新的模型供应商 THEN Meeting System SHALL 只需实现统一的适配器接口而无需修改核心逻辑
2. WHEN 核心会议逻辑执行 THEN Meeting System SHALL 与具体的 UI 实现和存储机制解耦
3. WHEN 系统组件交互 THEN Meeting System SHALL 通过明确定义的接口进行通信
4. WHEN 处理异步操作 THEN Meeting System SHALL 使用一致的错误处理和状态管理模式

### 需求 9

**用户故事:** 作为用户，我想要为每个会议指定一个主持人，以便有人负责组织会议进程和管理议题。

#### 验收标准

1. WHEN 用户创建会议 THEN Meeting System SHALL 允许用户指定主持人（可以是用户本人或参与会议的某个 AI 代理）
2. WHEN 会议开始 THEN Meeting System SHALL 将主持人的特殊职责添加到其上下文中
3. WHEN 主持人是 AI 代理 THEN Meeting System SHALL 在其系统提示词中添加主持人任务说明
4. WHEN 用户查看会议信息 THEN Meeting System SHALL 显示当前会议的主持人身份

### 需求 10

**用户故事:** 作为主持人，我想要管理会议议题列表，以便组织讨论内容和跟踪讨论进度。

#### 验收标准

1. WHEN 主持人创建会议 THEN Meeting System SHALL 允许主持人添加初始议题列表
2. WHEN 会议进行中 THEN Meeting System SHALL 允许主持人添加新议题
3. WHEN 会议进行中 THEN Meeting System SHALL 允许主持人删除或标记议题为已完成
4. WHEN 讨论偏离当前议题 THEN Meeting System SHALL 在主持人的上下文中包含提醒信息
5. WHEN 任何参与者发言 THEN Meeting System SHALL 将当前议题列表包含在其上下文中

### 需求 11

**用户故事:** 作为用户，我想要为会议配置讨论风格和偏好，以便控制会议的进行方式和参与者的行为。

#### 验收标准

1. WHEN 用户创建或配置会议 THEN Meeting System SHALL 允许用户设置讨论风格（如正式、轻松、辩论式）
2. WHEN 用户配置会议 THEN Meeting System SHALL 允许用户设置每个参与者的发言长度偏好（简短、中等、详细）
3. WHEN 代理准备发言 THEN Meeting System SHALL 将讨论风格和发言长度偏好注入到其系统提示词中
4. WHEN 用户更新会议配置 THEN Meeting System SHALL 在后续发言中应用新的配置

### 需求 12

**用户故事:** 作为用户，我想要系统将会议的关键信息注入到 AI 上下文中，以便代理能够了解会议状态和目标。

#### 验收标准

1. WHEN 代理准备发言 THEN Meeting System SHALL 将会议议题列表注入到其上下文中
2. WHEN 代理准备发言 THEN Meeting System SHALL 将当前会议结论（如果有）注入到其上下文中
3. WHEN 代理准备发言 THEN Meeting System SHALL 将该代理的角色描述注入到其系统提示词中
4. WHEN 主持人代理准备发言 THEN Meeting System SHALL 额外注入主持人的特殊任务和职责
5. WHEN 代理准备发言 THEN Meeting System SHALL 将所有参会者列表（包括姓名和角色）注入到其上下文中
6. WHEN 代理准备发言 THEN Meeting System SHALL 将会议主持人身份信息注入到其上下文中

### 需求 13

**用户故事:** 作为用户，我想要系统能够生成会议纪要，以便总结重要结论并减少后续对话的上下文长度。

#### 验收标准

1. WHEN 会议达成重要结论 THEN Meeting System SHALL 允许用户或主持人触发会议纪要生成
2. WHEN 生成会议纪要 THEN Meeting System SHALL 总结当前讨论的关键点、决策和待办事项
3. WHEN 会议纪要生成后 THEN Meeting System SHALL 将纪要保存到会议记录中
4. WHEN 会议纪要存在 THEN Meeting System SHALL 在后续发言的上下文中使用纪要而非全量历史消息
5. WHEN 使用会议纪要 THEN Meeting System SHALL 仍然包含纪要生成后的新消息作为上下文

### 需求 14

**用户故事:** 作为用户，我想要手动管理会议纪要，以便根据需要更新或重新生成纪要内容。

#### 验收标准

1. WHEN 用户请求生成纪要 THEN Meeting System SHALL 使用 AI 模型总结当前会议内容并创建纪要
2. WHEN 用户手动编辑纪要 THEN Meeting System SHALL 允许用户直接修改纪要文本内容
3. WHEN 用户请求 AI 更新纪要 THEN Meeting System SHALL 允许用户指定某个 AI 代理重新生成或更新纪要
4. WHEN 纪要被更新 THEN Meeting System SHALL 保留纪要的版本历史
5. WHEN 用户查看会议 THEN Meeting System SHALL 显示当前有效的会议纪要

### 需求 15

**用户故事:** 作为参会者，我想要能够提及（@）其他参会者，以便直接请求特定人员发言或回应。

#### 验收标准

1. WHEN 参会者发言时使用 @ 符号加参会者名称 THEN Meeting System SHALL 识别被提及的参会者
2. WHEN 消息中包含 @ 提及 THEN Meeting System SHALL 在被提及者的下次发言上下文中标注该提及
3. WHEN AI 代理被 @ 提及 THEN Meeting System SHALL 优先安排该代理作为下一个发言者
4. WHEN 用户被 @ 提及 THEN Meeting System SHALL 向用户发送通知或提示
5. WHEN 显示消息 THEN Meeting System SHALL 高亮显示 @ 提及内容

### 需求 16

**用户故事:** 作为用户，我想要首页能够展示最近进行中的会议，以便快速了解当前活动并继续参与。

#### 验收标准

1. WHEN 用户访问首页 THEN Meeting System SHALL 显示最近的进行中会议列表（最多 5 个）
2. WHEN 显示进行中会议 THEN Meeting System SHALL 包含会议主题、参与代理数量、消息数量和最后更新时间
3. WHEN 用户点击进行中会议 THEN Meeting System SHALL 直接跳转到该会议室
4. WHEN 没有进行中的会议 THEN Meeting System SHALL 显示友好的空状态提示
5. WHEN 进行中会议列表更新 THEN Meeting System SHALL 按最后更新时间降序排列

### 需求 17

**用户故事:** 作为用户，我想要在代理列表页面看到更详细的代理信息，以便更好地了解每个代理的特点和配置。

#### 验收标准

1. WHEN 用户查看代理列表 THEN Meeting System SHALL 显示每个代理的角色描述
2. WHEN 用户查看代理列表 THEN Meeting System SHALL 显示代理使用的模型供应商和模型名称
3. WHEN 代理角色描述较长 THEN Meeting System SHALL 提供展开/收起功能
4. WHEN 用户查看代理卡片 THEN Meeting System SHALL 使用视觉层次清晰展示代理名称、角色和模型信息
5. WHEN 代理列表为空 THEN Meeting System SHALL 显示引导用户创建第一个代理的提示

### 需求 18

**用户故事:** 作为用户，我想要会议界面中的设置类元素可以折叠，以便节省屏幕空间并专注于会议内容。

#### 验收标准

1. WHEN 用户进入会议室 THEN Meeting System SHALL 将会议信息面板（参与者、配置等）默认折叠在顶部
2. WHEN 用户点击会议信息面板标题 THEN Meeting System SHALL 展开或折叠面板内容
3. WHEN 会议信息面板折叠 THEN Meeting System SHALL 在标题栏显示关键信息摘要（参与者数量、状态）
4. WHEN 会议信息面板展开 THEN Meeting System SHALL 显示完整的参与者列表、配置和议题
5. WHEN 用户刷新页面 THEN Meeting System SHALL 记住面板的折叠/展开状态

### 需求 19

**用户故事:** 作为用户，我想要会议纪要可以作为图标折叠摆放，以便在需要时快速访问而不占用主要空间。

#### 验收标准

1. WHEN 会议存在纪要 THEN Meeting System SHALL 在界面右上角或固定位置显示纪要图标
2. WHEN 用户点击纪要图标 THEN Meeting System SHALL 以弹出面板或抽屉形式展示纪要内容
3. WHEN 纪要面板打开 THEN Meeting System SHALL 显示纪要内容、版本信息和操作按钮
4. WHEN 用户点击面板外部或关闭按钮 THEN Meeting System SHALL 关闭纪要面板
5. WHEN 会议没有纪要 THEN Meeting System SHALL 显示生成纪要的快捷入口图标

### 需求 20

**用户故事:** 作为用户，我想要议题列表悬浮在侧边并可收起，以便在讨论时随时查看议题而不影响消息阅读。

#### 验收标准

1. WHEN 会议有议题 THEN Meeting System SHALL 在左侧或右侧显示可收起的议题侧边栏
2. WHEN 用户点击收起按钮 THEN Meeting System SHALL 将议题侧边栏收起为图标或窄条
3. WHEN 议题侧边栏收起 THEN Meeting System SHALL 显示当前未完成议题数量的徽章
4. WHEN 用户点击展开按钮 THEN Meeting System SHALL 展开议题侧边栏显示完整列表
5. WHEN 议题状态更新 THEN Meeting System SHALL 实时更新侧边栏中的议题显示
6. WHEN 用户刷新页面 THEN Meeting System SHALL 记住侧边栏的展开/收起状态

### 需求 21

**用户故事:** 作为用户，我想要消息输入框占比更小并固定在底部，以便有更多空间查看会议消息历史。

#### 验收标准

1. WHEN 用户查看会议室 THEN Meeting System SHALL 将消息输入区域固定在页面底部
2. WHEN 消息输入区域显示 THEN Meeting System SHALL 限制其高度占比不超过屏幕的 20%
3. WHEN 用户滚动消息列表 THEN Meeting System SHALL 保持输入区域固定在底部不随滚动移动
4. WHEN 输入框获得焦点 THEN Meeting System SHALL 保持紧凑布局不扩展额外空间
5. WHEN 用户输入多行文本 THEN Meeting System SHALL 在输入框内部滚动而不扩展整体高度
