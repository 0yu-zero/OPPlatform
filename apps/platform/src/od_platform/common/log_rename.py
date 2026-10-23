#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : log_rename.py
# @Project   : ODPlatform / common
# @Function  : 日志归档 —— 把本次运行日志复制进推理输出目录并对齐命名
"""
rename_log_to_save_dir: 推理收尾时, 把 D2 根 logger (od_platform) 的 FileHandler
日志文件复制一份到 output_dir, 命名对齐训练侧习惯 (<model_stem>_infer.log).

重名自增 _2/_3/... (与 _resolve_output_dir 的 predict/predict2 行为对齐).
复制 (而非移动): FileHandler 还在写, 移动在 Windows 上会失败.
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Optional


def rename_log_to_save_dir(output_dir: Path, model_stem: str) -> Optional[Path]:
    """把当前进程日志复制到 output_dir/<model_stem>_infer.log (重名自增). 返回目标路径."""
    root = logging.getLogger("od_platform")
    src: Optional[Path] = None
    for h in root.handlers:
        if isinstance(h, logging.FileHandler):
            src = Path(h.baseFilename)
            break
    if src is None or not src.is_file():
        return None

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    base = output_dir / f"{model_stem}_infer"
    target = base.with_suffix(".log")
    n = 2
    while target.exists():
        target = base.with_name(f"{base.name}_{n}.log")
        n += 1

    try:
        shutil.copy2(src, target)
        return target
    except OSError as exc:
        logging.getLogger(__name__).warning(f"日志归档失败: {exc}")
        return None
