# 工具与来源：不要混淆三层验证

## 可信规则来源

1. simai 原作者 Celeca 的公开 Wiki：<https://w.atwiki.jp/simai/pages/1002.html>。原生记法规则优先采用该页；本 Skill 的语法速查为重新整理、并非全量复制。
2. Agent Skills 规范：<https://agentskills.io/specification>。需要 `SKILL.md` 及 YAML `name` / `description`。
3. GitHub Copilot Skills 安装指南：<https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills>。

## 可选第三方实现（需自行安装并核对版本）

- `lcebot/maidata-parser`：<https://github.com/lcebot/maidata-parser>。仓库文档介绍将 `maidata.txt` / 单谱 simai 转换为 `.ma2`，报告格式错误及部分可玩性冲突。其验证规则**是该项目的实现**，不等于官方标准；某些合法的 simai 高级用法也可能因目标引擎或版本不受支持。
- `Shikochin/simai-sharp-ts`：<https://github.com/Shikochin/simai-sharp-ts>。TypeScript 的 simai 解析与序列化实现，可用于工程性 round-trip 测试。README 与实际版本功能如不一致，以实际运行结果为准。
- 如有其他编辑器/模拟器（例如 AstroDX），以目标版本的文档和真实导入结果作为兼容性依据，不能凭 “simai” 三个字就保证全支持。

## 三层验证

1. **快检**：`python scripts/quick_lint.py ./maidata.txt`。仅检测文件结构、末尾 `E`、括号/部分时值等；不是完整解析器。
2. **语法/兼容**：用目标工具导入，或运行第三方 parser。注意可能存在原生语法支持差异。
3. **实际体验**：查音画同步、星形 SLIDE 起步等待、TOUCH 位置、区域冲突、视觉遮挡、难度手感。

最终报告须分别给出上述三层是否执行。没有做的保持“未验证”。

## Ponytail 约束

可配合 <https://github.com/DietrichGebert/ponytail> 贯彻：先复用已有解析器，只编写任务确实需要的最小脚本；但不要删减会造成隐性错误的测试与验收。它是**独立 Skill**，不是本 Skill 的运行依赖。
