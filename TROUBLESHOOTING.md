# 故障排查指南

## 常见问题及解决方案

### 1. AI 代理请求超时

**症状**: 点击"请求发言"后长时间等待，最后显示超时错误

**可能原因**:
- AI 服务商 API 响应慢
- 网络连接不稳定
- API Key 配额不足或被限流

**解决方案**:

1. **检查网络连接**
   ```bash
   # 测试是否能访问 AI 服务
   curl -I https://api.openai.com  # OpenAI
   curl -I https://open.bigmodel.cn  # GLM
   ```

2. **验证 API Key**
   - 登录 AI 服务商控制台检查 API Key 状态
   - 确认账户有足够的配额
   - 检查是否有速率限制

3. **增加超时时间**
   - GLM adapter 已设置为 120 秒超时
   - 如果仍然超时，可能是网络问题

4. **使用其他供应商**
   - 如果某个供应商持续超时，尝试使用其他供应商
   - OpenAI 和 Anthropic 通常响应较快

5. **检查后端日志**
   ```bash
   # 查看详细错误信息
   python -m uvicorn src.web.api:app --host 0.0.0.0 --port 8888 --reload
   ```

### 2. 消息不显示

**症状**: 发送消息后，会议室中看不到消息

**解决方案**:

1. **刷新页面**
   - 按 F5 或 Ctrl+R 刷新浏览器

2. **检查浏览器控制台**
   - 按 F12 打开开发者工具
   - 查看 Console 标签页是否有错误
   - 查看 Network 标签页检查 API 请求

3. **检查会议状态**
   - 确保会议状态是"进行中"
   - 如果是"已暂停"，点击"继续"按钮

4. **检查数据文件**
   ```bash
   # 查看会议数据是否保存
   ls -la data/meetings/
   cat data/meetings/[MEETING_ID].json
   ```

### 3. 前端无法连接后端

**症状**: 页面显示网络错误或无法加载数据

**解决方案**:

1. **确认后端已启动**
   ```bash
   # 访问后端健康检查
   curl http://localhost:8888
   # 应该返回: {"status":"ok","message":"AI Agent Meeting API"}
   ```

2. **检查端口占用**
   ```bash
   # macOS/Linux
   lsof -i :8888
   
   # 如果端口被占用，修改配置文件中的端口
   ```

3. **检查 CORS 配置**
   - 确认 `src/web/api.py` 中的 CORS 配置包含前端地址
   - 默认允许 `http://localhost:5173` 和 `http://localhost:3000`

4. **检查代理配置**
   - 查看 `web-frontend/vite.config.js` 中的 proxy 配置
   - 确保 target 指向正确的后端地址

### 4. WebSocket 连接失败

**症状**: 消息不会自动刷新，需要手动刷新页面

**解决方案**:

1. **检查 WebSocket 连接**
   - 打开浏览器开发者工具 (F12)
   - 查看 Network 标签页，筛选 WS (WebSocket)
   - 检查连接状态

2. **防火墙设置**
   - 确保防火墙允许 WebSocket 连接
   - 某些企业网络可能阻止 WebSocket

3. **使用手动刷新**
   - 即使 WebSocket 失败，手动刷新页面仍可查看最新消息
   - 代码已添加自动刷新功能

### 5. 代理测试连接失败

**症状**: 创建代理后，点击"测试"按钮显示失败

**解决方案**:

1. **验证 API Key**
   - 确保 API Key 正确无误
   - 注意不要有多余的空格

2. **检查模型名称**
   - OpenAI: `gpt-4`, `gpt-3.5-turbo`
   - Anthropic: `claude-3-opus-20240229`, `claude-3-sonnet-20240229`
   - Google: `gemini-pro`
   - GLM: `glm-4`, `glm-3-turbo`

3. **网络连接**
   - 确保能访问对应的 API 服务
   - 某些地区可能需要代理

### 6. 会议创建失败

**症状**: 点击创建会议后显示错误

**解决方案**:

1. **检查代理是否存在**
   - 确保选择的代理已成功创建
   - 在"代理管理"页面查看代理列表

2. **检查输入数据**
   - 会议主题不能为空
   - 至少选择一个代理
   - 最大轮次必须是正整数

3. **查看错误详情**
   - 错误消息会显示具体原因
   - 根据提示修正输入

### 7. 导出功能失败

**症状**: 点击导出按钮后没有下载文件

**解决方案**:

1. **检查浏览器设置**
   - 确保浏览器允许下载
   - 检查下载文件夹权限

2. **检查会议数据**
   - 确保会议有消息内容
   - 空会议也可以导出，但内容较少

3. **手动导出**
   ```bash
   # 使用 CLI 导出
   python -m src.cli.main meeting export [MEETING_ID] --format markdown -o meeting.md
   ```

## 性能优化建议

### 1. 减少 API 调用次数

- 避免频繁点击"请求发言"
- 等待上一个请求完成后再发起新请求
- 使用"发送消息"功能引导讨论方向

### 2. 控制会议规模

- 建议 2-4 个代理参与
- 设置合理的最大轮次（3-10 轮）
- 避免过长的消息内容

### 3. 选择合适的模型

- 快速响应: GPT-3.5-turbo, GLM-3-turbo
- 高质量: GPT-4, Claude-3-opus
- 平衡: Claude-3-sonnet, GLM-4

## 调试技巧

### 1. 启用详细日志

**后端日志**:
```bash
# 使用 --log-level debug
python -m uvicorn src.web.api:app --host 0.0.0.0 --port 8888 --reload --log-level debug
```

**前端日志**:
- 打开浏览器开发者工具 (F12)
- 查看 Console 标签页
- 代码中已添加 `console.log` 输出

### 2. 测试 API 端点

使用 Swagger UI 测试:
```
http://localhost:8888/docs
```

使用 curl 测试:
```bash
# 列出代理
curl http://localhost:8888/api/agents

# 列出会议
curl http://localhost:8888/api/meetings

# 获取会议详情
curl http://localhost:8888/api/meetings/[MEETING_ID]
```

### 3. 检查数据文件

```bash
# 查看所有代理
ls -la data/agents/

# 查看所有会议
ls -la data/meetings/

# 查看具体数据
cat data/agents/[AGENT_ID].json | python -m json.tool
cat data/meetings/[MEETING_ID].json | python -m json.tool
```

### 4. 清理测试数据

```bash
# 删除所有测试数据（谨慎操作！）
rm -rf data/agents/*
rm -rf data/meetings/*
```

## 获取帮助

如果以上方法都无法解决问题：

1. **收集信息**:
   - 错误消息截图
   - 浏览器控制台日志
   - 后端终端日志
   - 操作步骤

2. **运行测试**:
   ```bash
   python test_web_api.py
   ```

3. **提交 Issue**:
   - 包含上述收集的信息
   - 说明操作系统和 Python 版本
   - 描述期望行为和实际行为

## 已知问题

### GLM API 超时
- **问题**: GLM API 有时响应较慢，可能超过 120 秒
- **临时方案**: 重试请求或使用其他供应商
- **长期方案**: 考虑实现异步任务队列

### WebSocket 在某些环境下不稳定
- **问题**: 企业网络或某些代理可能阻止 WebSocket
- **临时方案**: 手动刷新页面查看最新消息
- **长期方案**: 实现轮询作为备选方案

### 大量消息时页面性能下降
- **问题**: 超过 100 条消息时滚动可能卡顿
- **临时方案**: 导出会议后创建新会议
- **长期方案**: 实现虚拟滚动或分页加载
