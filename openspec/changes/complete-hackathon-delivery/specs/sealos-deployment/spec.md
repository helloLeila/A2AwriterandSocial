## ADDED Requirements

### Requirement: Docker容器化
项目 SHALL 提供Dockerfile，支持单容器运行前后端。

#### Scenario: Docker本地构建验证
- **WHEN** 执行 docker build -t a2a-zhihu .
- **THEN** 镜像构建成功
- **AND** 执行 docker run -p 80:80 a2a-zhihu
- **AND** 访问 http://localhost 可看到前端页面
- **AND** 前端可正常调用 /api 和 /ws

### Requirement: Sealos云部署
项目 SHALL 支持一键部署到Sealos平台，提供可访问的线上链接。

#### Scenario: Sealos应用创建
- **WHEN** 在Sealos创建应用并配置镜像
- **THEN** 应用成功启动
- **AND** 提供公网可访问URL
- **AND** 环境变量（ANTHROPIC_API_KEY等）通过Sealos控制台配置
- **AND** 全流程可在线上体验

### Requirement: Nginx反向代理配置
Nginx SHALL 同时服务前端静态资源和代理后端API/WebSocket。

#### Scenario: 单入口访问
- **WHEN** 用户访问根路径 /
- **THEN** Nginx返回前端index.html和静态资源
- **WHEN** 请求 /api/* 路径
- **THEN** Nginx代理到本地uvicorn:8000
- **WHEN** 请求 /ws/* 路径
- **THEN** Nginx以WebSocket模式代理到本地uvicorn:8000
