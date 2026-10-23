#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : model_path.py
# @Project   : ODPlatform / common
# @Function  : 模型路径解析 —— 多目录查找, 找不到报可读错误
"""
resolve_model_path: 把"声明的模型名"解析成"真实存在的文件路径".

查找顺序 (每个目录下):
    1. 原样 (可能是绝对/相对路径或带后缀文件名)
    2. 无后缀时补 .pt
    3. 当作训练 run 目录, 找其下 best.pt / last.pt

找不到 → FileNotFoundError (调用方在 service 顶层 try 里兜成 InferResult.error).
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Union

PathLike = Union[str, Path]

_FALLBACK_WEIGHTS: tuple[str, ...] = ("best.pt", "last.pt")


def resolve_model_path(raw: PathLike, search_dirs: Iterable[PathLike]) -> Path:
    """raw: 声明的模型(文件名/路径/run 目录); search_dirs: 依次查找的目录."""
    p = Path(raw).expanduser()

    # 1) 绝对/相对路径直接命中
    if p.is_file():
        return p.resolve()

    # 候选文件名: 原样 + 无后缀补 .pt
    name_candidates = [p]
    if p.suffix == "":
        name_candidates.append(p.with_suffix(".pt"))

    for d in search_dirs:
        base = Path(d)
        for cand in name_candidates:
            f = cand if cand.is_absolute() else base / cand
            if f.is_file():
                return f.resolve()

    # 2) 当作训练 run 目录找权重
    for d in search_dirs:
        base = Path(d)
        run_dir = p if p.is_absolute() else base / p
        if run_dir.is_dir():
            for w in _FALLBACK_WEIGHTS:
                f = run_dir / w
                if f.is_file():
                    return f.resolve()

    searched = ", ".join(str(Path(d)) for d in search_dirs)
    raise FileNotFoundError(
        f"模型文件不存在: {raw!r} (已查找: {searched}; 支持 文件名/.pt 补全/run 目录下的 best.pt)"
    )
