# maimai-charting Agent Skill

用于舞萌 DX（maimai DX）的 simai/maidata 写谱、谱面解释、局部修改和检查。`SKILL.md` 是入口，其余说明按需读取。

## 安装

将整个 `maimai-charting` 文件夹复制到**项目级** `.agents/skills/maimai-charting/`，或个人级 `~/.agents/skills/maimai-charting/`（Windows 对应 `%USERPROFILE%\.agents\skills\maimai-charting`）。对于 GitHub Copilot 项目，也可使用 `.github/skills/maimai-charting/`；具体平台以其文档为准。

不要只复制 `SKILL.md`：参考文件与校验脚本也需要保持相对路径。

## 示例请求

- “使用 maimai-charting 技能，以 150 BPM 为基础给我写 8 小节的 MASTER 风格原创 simai 草稿，主要突出旋律与交互。暂不对轴。”
- “审查这份 maidata.txt 的语法和可玩性风险，不改变原来的音乐动机。”
- “把第 16–24 小节的 SLIDE 改得更自然，给出最小修改补丁。”

## 自检

```bash
python scripts/quick_lint.py assets/maidata-template.txt
python -m unittest discover -s tests -v
```

`quick_lint.py` 是**不完整的静态检查器**；“通过”只表示没有触发已经实现的结构规则。仍需外部解析器和试玩验证。Python 3.9+，无需第三方包。

## 参考

- [原生 simai 规则](https://w.atwiki.jp/simai/pages/1002.html)
- [Agent Skills 开放规范](https://agentskills.io/specification)
- [GitHub Copilot 安装文档](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)

## 版权

本目录中原创说明与脚本采用 MIT 许可；原始 simai 记谱规范与相关游戏/商标的权利归各自权利人。本项目不附带游戏素材、音乐或商业谱面。
