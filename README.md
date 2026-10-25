<div align="center">

# Quiver

### 求职季的开箱即用 Agent Skills —— 每个 skill 都对着一个真实痛点

[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](https://github.com/WsNodeX/quiver/actions)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/skills-4-9cf)](skills)
[![Dependencies](https://img.shields.io/badge/dependencies-0-lightgrey)](#)

**不是又一份提示词合集。每个 skill 都定义了完整的工作流程、输出格式和行为红线，装上就能用。**

</div>

---

## 这是什么

[Quiver](https://github.com/WsNodeX/quiver) 是一套面向**国内求职季开发者**的 Agent Skills 集合，遵循 [Agent Skills](https://modelcontextprotocol.io) 的 SKILL.md 开放格式，可以直接装进 Claude Code、WorkBuddy 等支持 skills 的 AI 客户端。

每个 skill 解决一个真实痛点：

| Skill | 痛点 | 一句话说明 |
|---|---|---|
| [`jd-decoder`](skills/jd-decoder) | JD 都是黑话，看不懂重点 | 把职位描述拆成硬性要求 / 隐含期待 / 面试考点 + 匹配度清单 |
| [`interview-grill`](skills/interview-grill) | 背了八股也不知道自己会不会 | 严格面试官多轮追问式模拟面试，结束给分维度评分 |
| [`resume-reviewer`](skills/resume-reviewer) | 简历石沉大海没人给改 | 按大厂筛选标准逐条改写，原文→改后→理由三列对照 |
| [`readme-booster`](skills/readme-booster) | 项目不错但 README 劝退 | 按高星项目排版标准重构 README，60 秒抓住陌生访客 |

> 💡 为什么选这四个？因为它们覆盖了求职的一条完整链路：**读懂岗位 → 练面试 → 改简历 → 装点作品集**。你不是在收集提示词，是在给自己配一套工作流。

---

## 🚀 快速开始

三种方式，选一个：

### 方式一：脚本安装（推荐）

```bash
git clone https://github.com/WsNodeX/quiver.git
cd quiver

# 装进 Claude Code（默认目标 ~/.claude/skills/）
python scripts/install.py --all

# 或装进 WorkBuddy（~/.workbuddy/skills/）
python scripts/install.py --all --client workbuddy

# 或只装某一个
python scripts/install.py jd-decoder
```

### 方式二：手动复制

把 `skills/` 下任意一个目录拷进客户端的 skills 目录即可：

```bash
cp -r skills/jd-decoder ~/.claude/skills/
```

### 方式三：验证一下再装

```bash
python scripts/validate.py   # 校验所有 skill 的格式合规性
```

装好之后，在客户端里说"帮我模拟面试"或"帮我看看这段 JD"，对应的 skill 就会被触发。

---

## 🧩 Skill 一览

### `jd-decoder` · JD 解码器

把一段招聘 JD 拆成六块可执行内容：岗位速览、硬性要求权重表、隐含期待（含推理依据）、面试考点预测、✅/⚠️/❌ 匹配度清单、一句话投递结论。核心原则是**区分"写了"和"会考"**，并诚实给出差距与最短补齐路径。

### `interview-grill` · 拷问官

扮演严格但有分寸的技术面试官：一次只问一个问题、按回答决定追问深度、连续答不上自动降档换角度。结束输出四维评分（基础 / 深度 / 场景 / 表达）和"背诵痕迹疑似点"——专治背了答案经不起追问。

### `resume-reviewer` · 简历手术刀

按"筛选者 30 秒停留"的标准审简历：动词开头、可验证量化、STAR 压缩、关键词命中，输出逐条改写对照表和今天改 / 本周改 / 可选的三级优先级。红线：不替你编数字，只教你把已有工作估成量级。

### `readme-booster` · README 增强器

按五维诊断（首屏三连、信任感、上手成本、专业感、图片引用）给出整份改写稿，而不是零碎建议。内置图片必须走 CDN 域名（GitHub 自动转 camo 代理、国内可达）这类实战细节。

---

## 🏗️ 目录结构

```
quiver/
├── skills/                  # 每个 skill 一个目录
│   ├── jd-decoder/
│   │   └── SKILL.md         # frontmatter(name/description) + 工作流正文
│   ├── interview-grill/
│   ├── resume-reviewer/
│   └── readme-booster/
├── scripts/
│   ├── validate.py          # 零依赖格式校验器（CI 同款）
│   └── install.py           # 一键安装到客户端 skills 目录
├── tests/                   # 26 个 unittest，覆盖校验与安装全部分支
└── .github/workflows/ci.yml # Python 3.10 / 3.13 双版本跑校验 + 测试
```

## 设计原则

- **工作流 > 提示词**：每个 skill 都写清"怎么一步步做"，而不是一句"你是一个资深 XX"。
- **输出格式固定**：skill 内置 Markdown 输出模板，每次产出结构一致，可直接对比多次结果。
- **行为红线**：明确写死"不做什么"（不编数据、不剧透答案、不一次抛十个问题），防止 skill 行为漂移。
- **零依赖**：校验器和安装脚本只用 Python 标准库，frontmatter 用手写解析器，不装 PyYAML。

## 🧪 测试

```bash
python scripts/validate.py                # 4/4 skill 格式合规
python -m unittest discover -s tests -v   # 26 个用例
```

CI 在 Python 3.10 与 3.13 两个版本上执行以上两步。

## 🗺️ 路线图

- [ ] 新增 `offer-compare`：多 offer 薪资/成长性对比决策
- [ ] 新增 `behavioral-coach`：HR 面行为问题（宝洁八大问类）打磨
- [ ] 支持 skill 多语言（中/英 frontmatter 与正文）
- [ ] 提供 skill 模板生成器 `python scripts/new.py <name>`

## 🤝 贡献

欢迎提交新 skill 或改进现有 skill。要求：SKILL.md 通过 `validate.py` 校验、工作流可复现、附上你实际用它的例子（Issue 里贴对话截图更好）。

## 📄 许可证

[MIT](LICENSE) © WsNodeX
