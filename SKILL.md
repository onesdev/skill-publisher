---
name: skill-publisher
version: 1.0.0
---

# skill-publisher

## 描述
自动将 WorkBuddy 本地 skill 复制到独立 Git 仓库目录，提交并推送代码及版本标签到远程仓库（如 GitHub、Gitee 等）。

**核心逻辑**：
1. 从 `~/.workbuddy/skills/` 查找源 skill
2. 将源 skill 复制到用户指定的独立 git 仓库目录
3. 在指定目录执行 git 提交、推送、打标签等操作

**重要**：不会在 WorkBuddy skills 目录下初始化 git，保持源码与使用环境分离。远程仓库地址需提前在目标目录中通过 `git remote add` 配置。

## 触发条件
当用户表达以下意图时触发：
- "发布 skill 到 GitHub"
- "帮我发布 skill"
- "把 skill 发布到仓库"
- "发布 xxx skill"
- "打包发布 skill"

## 参数

### 必需参数
- **skill_name**: 要发布的 skill 名称（在 `~/.workbuddy/skills/` 中查找）
- **repo_path**: 目标 Git 仓库目录的绝对路径（**不能**是 WorkBuddy skills 目录下的路径）

### 可选参数
- **version**: 版本号（如 1.0.0），默认从 SKILL.md 读取或询问用户
- **changelog**: 变更日志内容，默认空

## 使用步骤

1. 用户提供 skill_name（源 skill）和 repo_path（目标 git 仓库）
2. 如果信息不全，询问用户补充
3. 检查 repo_path 是否合法（不能在 WorkBuddy skills 目录下）
4. 执行发布流程：
   - 从 WorkBuddy skills 复制源 skill 到 repo_path
   - 在 repo_path 初始化 git（如需要）
   - 更新 SKILL.md 版本号（如需要）
   - 提交代码并打标签推送到已配置的远程仓库

## 工作目录分离

```
~/.workbuddy/skills/my-skill/      # 源 skill（只读，不修改）
         ↓ 复制
~/projects/my-skill-repo/          # Git 仓库（独立目录）
    ├── .git/
    ├── SKILL.md
    └── ...
```

## 执行命令

```bash
python publish.py --skill-name <skill_name> --repo-path <repo_path> \
  [--version <version>] [--changelog <changelog>]
```

## 注意事项

- **repo_path 不能是 WorkBuddy 或 OpenClaw 的 skills 目录**，必须是独立的 git 仓库目录
- 需要安装 git
- **远程仓库需提前配置**：在 repo_path 目录下通过 `git remote add origin <url>` 添加远程地址（支持 GitHub、Gitee 等任意 Git 托管平台）
- 推送时会自动推送 main 分支和版本标签
- 会根据 SKILL.md 中的版本号自动提取或询问用户

## 依赖

- git
- python3
