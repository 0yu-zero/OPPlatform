#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : style.py
# @Project   : ODPlatform / visualization
# @Function  : 绘制样式 (DrawStyle) —— 按帧尺寸自适应, yaml style 块可覆盖
"""
DrawStyle: 一次构造, 处处使用的"只读"绘制样式.

自适应策略: 不给 style 覆盖时, 框线粗细 / 标签字号按图像短边缩放——
小图不糊, 大图不至于线条细如发丝. yaml 里给了一个就完全以 yaml 为准.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Tuple


@dataclass(frozen=True)
class DrawStyle:
    """绘制样式 (颜色统一 BGR tuple)."""

    box_thickness: int = 2          # 框线粗细 (px)
    text_scale: float = 0.6         # 标签字号 (cv2 putText scale)
    text_color: Tuple[int, int, int] = (255, 255, 255)   # 标签字色 (白)
    text_bg_alpha: float = 0.6      # 标签背景不透明度 (0-1)

    # ------------------------------------------------------------------
    @classmethod
    def from_image_size(cls, h: int, w: int, **overrides: Any) -> "DrawStyle":
        """按帧尺寸自适应构造; overrides (yaml style 块) 优先级最高.

        自适应基准:
            box_thickness = min(h, w) / 300   (下限 1)
            text_scale    = min(h, w) / 800   (下限 0.4)
        """
        short = min(int(h), int(w))
        adaptive: dict[str, Any] = {
            "box_thickness": max(1, round(short / 300)),
            "text_scale": max(0.4, short / 800),
        }
        merged = {**adaptive, **(overrides or {})}
        # yaml list → tuple (颜色统一 tuple)
        if "text_color" in merged and not isinstance(merged["text_color"], tuple):
            merged["text_color"] = tuple(merged["text_color"])
        return cls(**merged)
