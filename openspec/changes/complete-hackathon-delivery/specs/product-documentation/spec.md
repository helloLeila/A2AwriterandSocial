## ADDED Requirements

### Requirement: README产品说明文档
项目 SHALL 包含README.md，阐述核心思路、技术方案及与知乎生态的契合度。

#### Scenario: 评委阅读README
- **WHEN** 评委打开GitHub仓库
- **THEN** 看到清晰的README
- **AND** 包含：项目标题、一句话描述、核心创新点、技术架构图/说明、Agent分工、4步流程、与知乎生态契合度说明、快速开始指南
- **AND** 技术架构说明区分社交主体Agent和后台工具Agent
- **AND** 明确强调「AI辅助、人为主导」价值观

### Requirement: 演示视频/截图（可选加分）
README SHOULD 包含GIF或截图展示4个面板。

#### Scenario: 快速理解产品
- **WHEN** 评委浏览README
- **THEN** 通过截图/GIF直观理解产品形态
- **AND** 无需运行代码即可get到核心价值
