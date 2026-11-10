<div align="center">

# Quiver

### 求职季的开箱即用 Agent Skills —— 每个 skill 都对着一个真实痛点

[![Stars](https://img.shields.io/github/stars/WsNodeX/quiver?style=flat-square&color=111111&label=stars)](https://github.com/WsNodeX/quiver/stargazers)
[![Release](https://img.shields.io/github/v/release/WsNodeX/quiver?style=flat-square&color=111111&label=release)](https://github.com/WsNodeX/quiver/releases)
[![License](https://img.shields.io/badge/license-MIT-111111?style=flat-square)](LICENSE)

</div>

---

面向**国内求职季开发者**的 Agent Skills 集合，遵循 SKILL.md 开放格式，可直接装进
Claude Code、WorkBuddy 等支持 skills 的客户端。

**不是又一份提示词合集**——每个 skill 都定义了完整的工作流程、固定输出格式和行为红线。

## 快速开始

```bash
git clone https://github.com/WsNodeX/quiver.git
cd quiver

python scripts/install.py --all                      # 装进 Claude Code (~/.claude/skills/)
python scripts/install.py --all --client workbuddy   # 装进 WorkBuddy
python scripts/install.py jd-decoder                 # 或只装某一个
```

装好后在客户端里说「帮我模拟面试」或「帮我看看这段 JD」，对应 skill 会自动触发。

手动安装也可以：把 `skills/` 下任意目录拷进客户端的 skills 目录。

```bash
cp -r skills/jd-decoder ~/.claude/skills/
```

## 四个 skill

| Skill | 痛点 | 一句话说明 |
|---|---|---|
| [`jd-decoder`](skills/jd-decoder) | JD 都是黑话，看不懂重点 | 拆成硬性要求 / 隐含期待 / 面试考点 + 匹配度清单 |
| [`interview-grill`](skills/interview-grill) | 背了八股也不知道自己会不会 | 严格面试官多轮追问式模拟面试，结束给四维评分 |
| [`resume-reviewer`](skills/resume-reviewer) | 简历石沉大海没人给改 | 按大厂筛选标准逐条改写，原文→改后→理由三列对照 |
| [`readme-booster`](skills/readme-booster) | 项目不错但 README 劝退 | 按高星项目排版标准重构 README |

这四个覆盖一条完整链路：**读懂岗位 → 练面试 → 改简历 → 装点作品集**。

### `jd-decoder`

把一段 JD 拆成六块可执行内容：岗位速览、硬性要求权重表、隐含期待（含推理依据）、
面试考点预测、✅/⚠️/❌ 匹配度清单、一句话投递结论。核心原则是**区分「写了」和
「会考」**，并诚实给出差距与最短补齐路径。

### `interview-grill`

扮演严格但有分寸的技术面试官：一次只问一个问题、按回答决定追问深度、连续答不上
自动降档换角度。结束输出四维评分（基础 / 深度 / 场景 / 表达）和「背诵痕迹疑似点」
——专治背了答案经不起追问。

### `resume-reviewer`

按「筛选者 30 秒停留」的标准审简历：动词开头、可验证量化、STAR 压缩、关键词命中，
输出逐条改写对照表。红线是**不替你编数字**，只教你把已有工作估成量级。

### `readme-booster`

按五维诊断（首屏三连、信任感、上手成本、专业感、图片引用）给出整份改写稿，而不是
零碎建议。姊妹项目 [readme-forge](https://github.com/WsNodeX/readme-forge) 把同一套
标准做成了可执行的审计脚本。

## 工作流

```mermaid
graph LR
  A[读 JD] -->|jd-decoder| B[匹配度清单]
  B -->|resume-reviewer| C[改写后的简历]
  C -->|interview-grill| D[四维评分]
  D -->|readme-booster| E[作品集]
```

## 目录结构

```
quiver/
├── skills/                  # 每个 skill 一个目录
│   ├── jd-decoder/SKILL.md  # frontmatter(name/description) + 工作流正文
│   ├── interview-grill/
│   ├── resume-reviewer/
│   └── readme-booster/
├── scripts/
│   ├── validate.py          # 零依赖格式校验器（CI 同款）
│   └── install.py           # 一键安装到客户端 skills 目录
├── tests/                   # unittest，覆盖校验与安装全部分支
└── .github/workflows/ci.yml # Python 3.10 / 3.13 双版本跑校验 + 测试
```

## 设计原则

- **工作流 > 提示词**：每个 skill 写清「怎么一步步做」，而不是一句「你是一个资深 XX」。
- **输出格式固定**：内置 Markdown 输出模板，每次产出结构一致，可直接对比多次结果。
- **行为红线**：明确写死「不做什么」（不编数据、不剧透答案、不一次抛十个问题），
  防止 skill 行为漂移。
- **零依赖**：校验器和安装脚本只用标准库，frontmatter 用手写解析器，不装 PyYAML。

## 测试

```bash
python scripts/validate.py                # 4/4 skill 格式合规
python -m unittest discover -s tests -v   # 全部用例
```

CI 在 Python 3.10 与 3.13 上执行以上两步。

## 限制

- **中文场景为主。** skill 的提示词和输出模板是国内求职语境写的，英文市场需要改写。
- **它给建议，不给结果。** 简历里的量化数字必须你自己填——skill 刻意不代劳，因为
  编出来的数字会在面试里露馅。
- **依赖客户端支持 skills。** 不支持的客户端只能当普通提示词用，效果打折。

## 路线图

- [ ] `offer-compare`：多 offer 薪资 / 成长性对比决策
- [ ] `behavioral-coach`：HR 面行为问题打磨
- [ ] skill 多语言（中 / 英 frontmatter 与正文）
- [ ] `python scripts/new.py <name>` 生成新 skill 模板

## 许可证

[MIT](LICENSE)
