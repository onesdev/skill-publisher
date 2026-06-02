#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Publisher - 将 WorkBuddy 本地 skill 复制到独立 Git 仓库并推送到远程
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """执行 shell 命令并返回结果"""
    print(f"执行: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    if check and result.returncode != 0:
        print(f"错误: {result.stderr}", file=sys.stderr)
        return None
    return result.stdout.strip()


def find_skill_dir(skill_name):
    """查找 skill 目录"""
    skill_paths = [
        Path.home() / ".workbuddy" / "skills" / skill_name,
        Path.home() / ".openclaw" / "skills" / skill_name,
        Path.cwd() / skill_name,
    ]

    for path in skill_paths:
        if path.exists() and path.is_dir():
            return path

    search_paths = [
        Path.home() / ".workbuddy" / "skills",
        Path.home() / ".openclaw" / "skills",
    ]

    for search_path in search_paths:
        if search_path.exists():
            for item in search_path.iterdir():
                if item.is_dir() and item.name.lower() == skill_name.lower():
                    return item

    return None


def copy_skill_files(skill_dir, repo_dir):
    """复制 skill 文件到仓库目录"""
    print(f"复制文件: {skill_dir} -> {repo_dir}")

    repo_dir = Path(repo_dir)
    repo_dir.mkdir(parents=True, exist_ok=True)

    for item in skill_dir.iterdir():
        if item.name == ".git":
            continue

        target = repo_dir / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)

    print(f"文件复制完成: {len(list(skill_dir.iterdir()))} 个项目")
    return True


def check_git_initialized(repo_dir):
    """检查 git 是否已初始化"""
    git_dir = Path(repo_dir) / ".git"
    return git_dir.exists()


def init_git(repo_dir):
    """初始化 git 仓库"""
    print("初始化 git 仓库...")

    result = run_command("git init", cwd=repo_dir)
    if result is None:
        return False

    run_command("git branch -M main", cwd=repo_dir, check=False)

    print("git 初始化完成")
    return True


def extract_version_from_skillmd(skillmd_path):
    """从 SKILL.md 提取版本号"""
    if not skillmd_path.exists():
        return None

    content = skillmd_path.read_text(encoding="utf-8")

    patterns = [
        r'version[:\s]+v?(\d+\.\d+\.\d+)',
        r'##\s*Version[:\s]+v?(\d+\.\d+\.\d+)',
        r'##\s*版本[:\s]+v?(\d+\.\d+\.\d+)',
        r'v?(\d+\.\d+\.\d+)\s*-',
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def update_skillmd_version(skillmd_path, version, changelog=""):
    """更新 SKILL.md 中的版本号和变更日志"""
    if not skillmd_path.exists():
        return False

    content = skillmd_path.read_text(encoding="utf-8")

    if f"version: {version}" not in content and f"## 版本" not in content:
        new_section = f"\n\n## 版本 {version}\n\n{changelog if changelog else '首次发布'}"
        content += new_section

        skillmd_path.write_text(content, encoding="utf-8")
        print(f"已更新 SKILL.md 版本为: {version}")
        return True

    return True


def commit_and_tag(repo_dir, version):
    """提交代码并打标签"""
    print("提交代码...")

    result = run_command("git add .", cwd=repo_dir)
    if result is None:
        return False

    result = run_command(f'git commit -m "chore: release v{version}"', cwd=repo_dir, check=False)
    if result is None:
        print("没有需要提交的变更，或提交失败")

    result = run_command("git push origin main", cwd=repo_dir, check=False)
    if result is None:
        print("推送失败，可能需要先配置 remote 或登录")
        return False

    tag_name = f"v{version}"
    result = run_command(f"git tag {tag_name}", cwd=repo_dir)
    if result is None:
        return False

    result = run_command(f"git push origin {tag_name}", cwd=repo_dir)
    if result is None:
        return False

    print(f"标签 {tag_name} 已推送")
    return True


def is_in_skills_directory(path):
    """检查路径是否在 WorkBuddy 或 OpenClaw 的 skills 目录下"""
    path = Path(path).resolve()

    forbidden_patterns = [
        Path.home() / ".workbuddy" / "skills",
        Path.home() / ".openclaw" / "skills",
    ]

    for pattern in forbidden_patterns:
        try:
            path.relative_to(pattern)
            return True
        except ValueError:
            continue

    return False


def validate_repo_path(repo_path):
    """验证 repo_path 是否合法"""
    path = Path(repo_path)

    if is_in_skills_directory(path):
        print(f"错误: repo_path 不能在 WorkBuddy 或 OpenClaw 的 skills 目录下")
        print(f"当前路径: {path}")
        print(f"请指定一个独立的目录，例如:")
        print(f"  - ~/projects/my-skill")
        print(f"  - D://projects//my-skill")
        print(f"  - C://Users//{os.getlogin()}//git//my-skill")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Skill Publisher")
    parser.add_argument("--skill-name", required=True, help="Skill 名称（源 skill，在 ~/.workbuddy/skills/ 中）")
    parser.add_argument("--repo-path", required=True, help="目标 Git 仓库目录（必须是独立目录，不能在 skills 下）")
    parser.add_argument("--version", help="版本号")
    parser.add_argument("--changelog", help="变更日志")

    args = parser.parse_args()

    print(f"开始发布 skill: {args.skill_name}")
    print(f"目标仓库: {args.repo_path}")

    if not validate_repo_path(args.repo_path):
        return 1

    skill_dir = find_skill_dir(args.skill_name)
    if not skill_dir:
        print(f"错误: 找不到 skill '{args.skill_name}'")
        print(f"已搜索以下位置:")
        print(f"  - ~/.workbuddy/skills/{args.skill_name}")
        print(f"  - ~/.openclaw/skills/{args.skill_name}")
        print(f"请检查 skill 名称是否正确，或提供完整路径")
        return 1

    print(f"找到 skill 目录: {skill_dir}")

    if not copy_skill_files(skill_dir, args.repo_path):
        return 1

    if not check_git_initialized(args.repo_path):
        print("git 未初始化，正在初始化...")
        if not init_git(args.repo_path):
            return 1
    else:
        print("git 已初始化")

    skillmd_path = Path(args.repo_path) / "SKILL.md"
    version = args.version

    if not version:
        version = extract_version_from_skillmd(skillmd_path)
        if version:
            print(f"从 SKILL.md 读取到版本号: {version}")
        else:
            print("错误: 未提供版本号，且 SKILL.md 中未找到版本信息")
            print("请使用 --version 参数指定版本号")
            return 1

    if args.version or args.changelog:
        update_skillmd_version(skillmd_path, version, args.changelog or "")

    if not commit_and_tag(args.repo_path, version):
        return 1

    print(f"\n✅ Skill '{args.skill_name}' 发布流程已完成！")
    print(f"版本: v{version}")
    print(f"代码及标签已推送到远程仓库")

    return 0


if __name__ == "__main__":
    sys.exit(main())
