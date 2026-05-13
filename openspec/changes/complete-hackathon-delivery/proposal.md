## Why

知乎AI黑客松A2A社交赛道作品交付截止时间为5月14日13:00。当前项目后端4步Agent流程已完成，但前端UI完全缺失（无App.tsx、无组件）、无部署方案、无产品说明文档。必须补齐前端可视化界面（1:1复刻知乎UI风格+4个演示面板）、Sealos云部署配置和产品README，才能形成可演示的完整参赛作品。

## What Changes

- **新增前端完整UI**：基于React+TypeScript+Vite构建4个演示面板（话题启动区、A2A实时社交日志、需求对齐看板、创作者辅助输出），视觉风格1:1复刻知乎原生UI（蓝白配色、卡片布局、字体系统）。
- **新增部署配置**：创建Dockerfile、Sealos部署配置，支持一键部署到Sealos云原生平台，提供可访问的线上Demo链接。
- **新增产品说明文档**：撰写README.md，阐述核心思路、技术方案、与知乎生态的契合度，满足评委必交材料要求。
- **前端补齐缺失文件**：创建App.tsx及所有组件，修复当前前端目录仅有main.tsx和vite-env.d.ts的空白状态。

## Capabilities

### New Capabilities
- `zhihu-ui-frontend`: 1:1复刻知乎原生UI风格的前端界面，包含4个演示面板和WebSocket实时通信。
- `sealos-deployment`: 基于Docker的Sealos云原生部署方案，提供可访问的线上Demo。
- `product-documentation`: 产品说明文档（README），阐述技术方案与知乎生态契合度。

### Modified Capabilities
- （无现有spec需要修改）

## Impact

- **前端**: 新增App.tsx、components/目录、types/目录、hooks/目录、styles/全局样式。
- **后端**: 无需修改，现有FastAPI+WebSocket API可直接被新前端消费。
- **部署**: 新增Dockerfile、.dockerignore、sealos部署配置。
- **文档**: 新增README.md（产品说明介绍）。
