#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : __init__.py
# @Project   : ODPlatform / visualization
# @Function  : visualization 包入口 —— 对外只暴露 BeautifyVisualizer / DrawStyle
"""ODPlatform 美化绘制包 (D7 推理子系统前置).

用法:
    from od_platform.visualization import BeautifyVisualizer, DrawStyle

    viz = BeautifyVisualizer(labels=class_names, label_mapping={...})
    style = DrawStyle.from_image_size(h, w, **style_overrides)
    annotated = viz.draw(image, dets, style=style, use_label_mapping=True)
"""
from .beautify import BeautifyVisualizer, Detections
from .style import DrawStyle

__all__ = [
    "BeautifyVisualizer",
    "DrawStyle",
    "Detections",
]
