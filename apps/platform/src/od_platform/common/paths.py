#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : paths.py
# @Author    : ODPlatform Team
# @Project   : ODPlatform
# @Function  : 集中定义项目路径常量
#              - 使用 marker file 模式定位 ROOT_DIR(workspace 根)
#              - 引入 APP_DIR 概念,把【共享资产】和【端私有资产】分开

from pathlib import Path
from typing import List, Tuple

# ============================================================
# Workspace 根目录定位 (marker file 模式)
# ============================================================
WORKSPACE_MARKER: str = ".odp-workspace"


def _find_workspace_root(
    start: Path,
    markers: Tuple[str, ...] = (WORKSPACE_MARKER,),
) -> Path:
    """
    从 start 开始沿父目录向上查找,返回包含任一 marker 文件的目录。

    Args:
        start: 起始路径(通常是 Path(__file__))
        markers: 一组 marker 文件名,任一存在即视为找到

    Returns:
        Path: workspace 根目录

    Raises:
        FileNotFoundError: 一直爬到文件系统根仍没找到
    """
    current = start.resolve()
    if current.is_file():
        current = current.parent

    for parent in [current, *current.parents]:
        for marker in markers:
            if (parent / marker).exists():
                return parent

    raise FileNotFoundError(
        f"找不到 workspace marker 文件 ({markers})。"
        f"请确认仓库根存在 {WORKSPACE_MARKER} 文件。"
    )


# 计算 ROOT_DIR(模块加载时执行一次)
ROOT_DIR: Path = _find_workspace_root(Path(__file__))


# ============================================================
# 端根目录 APP_DIR (platform 这一个端的根)
# ============================================================
APP_DIR: Path = ROOT_DIR / "apps" / "platform"


# ============================================================
# 【共享资产】(在 ROOT_DIR 下,所有端可访问)
# ============================================================
DATA_DIR: Path = ROOT_DIR / "data"
MODELS_DIR: Path = ROOT_DIR / "models"
RUNS_DIR: Path = ROOT_DIR / "runs"

# 模型子目录
PRETRAINED_MODELS_DIR: Path = MODELS_DIR / "pretrained"  # 下载的预训练权重(输入)
TRAINED_MODELS_DIR: Path = MODELS_DIR / "trained"        # 训练产出、长期保留的权重(产物)

# 数据集子目录
# 设计依据见 D0 决定 5:原始(只读)与派生(可再生)分家。
# train/val/test 划分属于派生产物,会在数据处理那天用固定种子一次性
# 冻结进 processed/ 内;init 阶段只建 raw / processed 两个空目录。
RAW_DATA_DIR: Path = DATA_DIR / "raw"              # 原始数据:只读,绝不就地改
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"  # 派生数据集:含冻结后的 train/val/test


# ============================================================
# 【端私有资产】(在 APP_DIR 下,只属于 platform 这个端)
# ============================================================
CONFIGS_DIR: Path = APP_DIR / "configs"
LOGGING_DIR: Path = APP_DIR / "logging"
UNIT_TEST_DIR: Path = APP_DIR / "tests"


# ============================================================
# 【顶层文档目录】(共享给所有人)
# ============================================================
DOCS_DIR: Path = ROOT_DIR / "docs"


# ============================================================
# 【工程基础设施目录】(共享)
# ============================================================
SCRIPTS_DIR: Path = ROOT_DIR / "scripts"

# ============================================================
# 【工具元数据目录】(审计日志等工具自身数据)
# ============================================================
META_DIR: Path = ROOT_DIR / ".odp-meta"
META_LOGGING_DIR: Path = META_DIR / "logs"


# ============================================================
# 对外暴露的"要初始化的目录列表"
# ============================================================
def get_dirs_to_initialize() -> List[Path]:
    """
    返回项目启动时需要确保存在的所有目录列表。

    这是 init_project.py 的【唯一数据源】——
    paths.py 决定要哪些目录,init_project 只负责创建。

    Returns:
        所有需要初始化的目录路径列表
    """
    return [
        # 共享资产
        DATA_DIR,
        RUNS_DIR,
        MODELS_DIR,
        PRETRAINED_MODELS_DIR,
        TRAINED_MODELS_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        # 端私有资产
        CONFIGS_DIR,
        LOGGING_DIR,
        UNIT_TEST_DIR,
        # 工程基础设施
        SCRIPTS_DIR,
        DOCS_DIR,
        # 元工具审计日志,不属于业务 reset 清理范围
        META_LOGGING_DIR,
    ]


def _get_reset_children(directory: Path) -> List[Path]:
    """返回可清理的直接子项,保留目录中的 Git 跟踪 README。"""
    if not directory.exists():
        return []

    return [
        path
        for path in directory.iterdir()
        if path.name != "README.md"
    ]


def get_paths_to_reset() -> List[Path]:
    """
    返回 reset_project 可以安全删除的路径列表。

    和 get_dirs_to_initialize 的关键差异:
        - init:  "启动时要确保存在的目录"——可能含 git 追踪目录(如 docs/)
        - reset: "可以被清理的运行时产物路径"——不包含 Git 跟踪文件

    安全原则:
        ✅ 只列【.gitignore 忽略的】运行时产物
        ❌ 不列 Git 跟踪文件(如 runs/README.md 和 models/trained/README.md)
        ❌ 用户的【原始数据】(RAW_DATA_DIR)绝不列入

    runs/ 和 models/trained/ 中有 Git 跟踪的 README,因此只列它们的直接子项,
    不能把父目录本身交给删除操作。
    """
    paths: List[Path] = [
        # 这些目录没有 Git 跟踪文件,可以整体清理
        PROCESSED_DATA_DIR,
        # 逐项清理,保留目录中的 README.md
        *_get_reset_children(RUNS_DIR),
        *_get_reset_children(TRAINED_MODELS_DIR),
        # 由 reset 执行器在关闭项目日志 handlers 后最后清理
        LOGGING_DIR,
        # 注意:以下目录【不在】 reset 范围内——
        #   RAW_DATA_DIR           : 用户辛苦准备的原始数据,reset 绝不碰
        #   PRETRAINED_MODELS_DIR  : 预训练权重(下载来的输入,很大,重下载耗时)
        #   CONFIGS_DIR / UNIT_TEST_DIR / SCRIPTS_DIR / DOCS_DIR : 都进 git
        #   META_DIR               : reset/doctor 等元工具的审计数据
    ]
    return [path for path in paths if not is_protected(path)]


# ============================================================
# 【绝对保护目录】reset 工具永远不能删除这些
# ============================================================
# 这是【最后一道安全网】——即使 get_paths_to_reset() 写错了,
# reset 也会拒绝删除这些目录。
PROTECTED_DIRS: tuple[Path, ...] = (
    ROOT_DIR,
    ROOT_DIR / "apps",
    ROOT_DIR / "packages",
    APP_DIR,
    APP_DIR / "src",
    SCRIPTS_DIR,
    DOCS_DIR,
    UNIT_TEST_DIR,
    CONFIGS_DIR,
    RAW_DATA_DIR,
    PRETRAINED_MODELS_DIR,
    META_DIR,
    META_LOGGING_DIR,
    ROOT_DIR / ".git",
    ROOT_DIR / ".odp-workspace",
)


def is_protected(path: Path) -> bool:
    """
    路径是否受保护(任一满足即受保护):
        1. 路径本身在 PROTECTED_DIRS 中
        2. 路径是某个 PROTECTED_DIRS 成员的【祖先目录】
           (例如 ROOT_DIR 是 SCRIPTS_DIR 的祖先——删 ROOT_DIR
            就连带删了 SCRIPTS_DIR,所以删祖先也得拦)
    """
    path = path.resolve(strict=False)
    for protected in PROTECTED_DIRS:
        protected_resolved = protected.resolve(strict=False)
        if path == protected_resolved:
            return True
        if protected_resolved.is_relative_to(path):
            return True
    return False


if __name__ == "__main__":
    print(f"ROOT_DIR (workspace) = {ROOT_DIR}")
    print(f"APP_DIR  (platform)  = {APP_DIR}")
    print(f"\n共享资产:")
    print(f"  DATA_DIR    = {DATA_DIR.relative_to(ROOT_DIR)}")
    print(f"  MODELS_DIR  = {MODELS_DIR.relative_to(ROOT_DIR)}")
    print(f"  RUNS_DIR    = {RUNS_DIR.relative_to(ROOT_DIR)}")
    print(f"\n端私有资产:")
    print(f"  CONFIGS_DIR = {CONFIGS_DIR.relative_to(ROOT_DIR)}")
    print(f"  LOGGING_DIR = {LOGGING_DIR.relative_to(ROOT_DIR)}")

    print(f"\n要初始化的目录共 {len(get_dirs_to_initialize())} 个:")
    for d in get_dirs_to_initialize():
        print(f"  - {d.relative_to(ROOT_DIR)}")