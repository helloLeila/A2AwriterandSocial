## Context

后端已完成：FastAPI + 4个Agent（Collector、Filter、User、Answerer）+ SessionOrchestrator + WebSocket实时推送。前端当前仅有main.tsx，App.tsx缺失，用户无法交互。部署为零，README为零。必须在<24小时内补齐。

## Goals / Non-Goals

**Goals:**
- 构建可运行的前端UI，4个面板完整展示A2A全流程
- 视觉风格1:1贴合知乎（蓝白配色、卡片、字体、圆角）
- 部署到Sealos，提供可访问的线上Demo链接
- 撰写README满足评委材料要求

**Non-Goals:**
- 不修改后端Agent逻辑（已完成，无需改动）
- 不做用户登录/OAuth（时间不够，影响人气奖但不影响核心评分）
- 不做持久化存储（内存会话足够Demo）

## Decisions

**前端状态管理：纯React useState + useEffect，不用Redux/Zustand**
- 理由：组件层级浅，WebSocket是唯一数据源，useState足够
- 替代方案：Zustand — 引入成本和收益不成正比

**样式方案：纯CSS（无Tailwind/Styled-components）**
- 理由：知乎UI需要精确像素级复刻，纯CSS最可控；无额外依赖；打包体积小
- 替代方案：Tailwind — 知乎UI的自定义细节（阴影、边框、特定色值）用Tailwind反而啰嗦

**部署：Sealos云原生平台**
- 理由：主办方推荐/参赛者常用；支持Docker一键部署；有免费额度
- 方案：单容器部署，Nginx反向代理前端静态资源，同时通过location /api和/ws转发到后端uvicorn

**前后端同容器部署 vs 分离部署**
- 选择：同容器（Nginx + uvicorn）
- 理由：Sealos单应用即可运行，配置简单，CORS问题消失；Demo场景不需要高可用分离

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| 时间不足，无法精细化复刻知乎UI | 优先保证4个面板功能完整，视觉用知乎色值+卡片布局快速逼近 |
| Anthropic API调用费用/速率限制 | Demo预准备几组固定case，必要时可mock LLM响应 |
| Sealos部署踩坑 | 预留最后2小时专门处理部署，先用本地docker验证 |
| WebSocket在Sealos反向代理下不通 | Nginx配置显式upgrade websocket头 |

## Migration Plan

1. 本地开发完成前端（npm run dev + python main.py）
2. 本地Docker构建验证：`docker build -t a2a-zhihu . && docker run -p 80:80`
3. 推送镜像到Docker Hub
4. Sealos创建应用，拉取镜像，配置环境变量
5. 测试线上Demo全流程
6. 提交作品链接

## Open Questions

- 是否需要在Demo中预置几个知乎问题链接供评委快速体验？（建议：是，准备3-5个热榜问题URL）
