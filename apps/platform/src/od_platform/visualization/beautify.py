#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : beautify.py
# @Project   : ODPlatform / visualization
# @Function  : 美化绘制器 (BeautifyVisualizer) —— 画框 + 中文标签 (PIL 绘字)
"""
BeautifyVisualizer: YOLO 原生 plot() 的美化替代品.

- 框: cv2.rectangle, 颜色按类别映射 (color_mapping → default_color → 内置调色盘)
- 标签: "显示名 置信度"; 显示名走 label_mapping (英→中), 用 PIL 绘字支持中文
- 纯 ASCII 标签走 cv2.putText 快路径; 含中文才整帧转 PIL (懒转换, 不白花开销)

依赖方向: 本模块是纯工具层, 不 import 宿主任何其他子包.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# 内置调色盘 (BGR, 高饱和度易区分) —— 类别不在 color_mapping 里时按索引轮换
_DEFAULT_PALETTE: Tuple[Tuple[int, int, int], ...] = (
    (0, 255, 0),      # 绿
    (0, 0, 255),      # 红
    (255, 128, 0),    # 橙
    (0, 255, 255),    # 黄
    (255, 0, 180),    # 玫红
    (200, 150, 50),   # 棕
    (255, 255, 0),    # 青
    (128, 0, 255),    # 紫
)


# ============================================================================
# 检测结果载体 (与 ultralytics 解耦的最小数据结构)
# ============================================================================
@dataclass
class Detections:
    """一帧的检测集合. boxes: (N,4) xyxy; confidences: (N,); labels: N 个类别名."""

    boxes: np.ndarray
    confidences: np.ndarray
    labels: List[str] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.labels)


# ============================================================================
# 美化绘制器
# ============================================================================
class BeautifyVisualizer:
    """按类别上色 + 中文标签绘制. 线程约定: 只在 render 线程调用 draw()."""

    def __init__(
        self,
        labels: Sequence[str],
        label_mapping: Optional[Dict[str, str]] = None,
        color_mapping: Optional[Dict[str, Tuple[int, int, int]]] = None,
        default_color: Optional[Tuple[int, int, int]] = None,
        font_path: Optional[str] = None,
    ) -> None:
        self.labels: List[str] = list(labels)
        self.label_mapping: Dict[str, str] = dict(label_mapping or {})
        self.color_mapping: Dict[str, Tuple[int, int, int]] = {
            k: tuple(v) for k, v in (color_mapping or {}).items()
        }
        self.default_color: Tuple[int, int, int] = tuple(default_color) if default_color else (0, 255, 0)
        self.font_path: Optional[str] = font_path
        self._font: Any = None            # PIL ImageFont, 懒加载
        self._font_failed: bool = False   # 字体加载失败只报一次

    # ------------------------------------------------------------------
    # 工厂: 从 ultralytics result 解包出来的原始数组构造
    # ------------------------------------------------------------------
    @staticmethod
    def from_yolo_results(
        boxes: np.ndarray,
        confidences: np.ndarray,
        labels: List[str],
    ) -> Detections:
        """boxes (N,4) xyxy + confidences (N,) + labels (N 个类别名) → Detections."""
        return Detections(
            boxes=np.asarray(boxes).reshape(-1, 4),
            confidences=np.asarray(confidences).reshape(-1),
            labels=list(labels),
        )

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------
    def draw(
        self,
        image: np.ndarray,
        dets: Detections,
        style: Any = None,
        use_label_mapping: bool = True,
    ) -> np.ndarray:
        """把 dets 画到 image (BGR) 上, 返回标注后的新数组 (不改入参)."""
        from .style import DrawStyle

        st = style or DrawStyle()
        out = image.copy()
        h, w = out.shape[:2]

        # 先算好每条的 (显示名, 颜色); 有中文才走 PIL 路径
        entries: List[Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int], str]] = []
        need_pil = False
        for i, label in enumerate(dets.labels):
            x1, y1, x2, y2 = (int(v) for v in dets.boxes[i])
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w - 1, x2), min(h - 1, y2)
            name = label
            if use_label_mapping and self.label_mapping:
                name = self.label_mapping.get(label, label)
            conf = float(dets.confidences[i]) if i < len(dets.confidences) else None
            text = f"{name} {conf:.2f}" if conf is not None else name
            if not need_pil and any(ord(c) > 127 for c in text):
                need_pil = True
            entries.append(((x1, y1), (x2, y2), self._color_for(label), text))

        # 画框 (cv2)
        for p1, p2, color, _ in entries:
            cv2.rectangle(out, p1, p2, color, st.box_thickness)

        # 画标签
        if entries:
            if need_pil:
                out = self._draw_labels_pil(out, entries, st)
            else:
                self._draw_labels_cv(out, entries, st)
        return out

    # ------------------------------------------------------------------
    def _color_for(self, label: str) -> Tuple[int, int, int]:
        """类别 → BGR: color_mapping 优先, 其次 default_color, 最后内置调色盘."""
        if label in self.color_mapping:
            return self.color_mapping[label]
        if self.color_mapping:
            # 有映射但没这个类别 → default_color
            return self.default_color
        try:
            idx = self.labels.index(label)
        except ValueError:
            idx = 0
        return _DEFAULT_PALETTE[idx % len(_DEFAULT_PALETTE)]

    # ------------------------------------------------------------------
    @staticmethod
    def _draw_labels_cv(
        image: np.ndarray,
        entries: Sequence[Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int], str]],
        st: Any,
    ) -> None:
        """纯 ASCII 标签: cv2.putText + 半透明背景."""
        overlay = image.copy()
        for p1, _p2, _color, text in entries:
            org = (p1[0], max(st.text_scale * 22, p1[1] - 4))
            cv2.putText(overlay, text, org, cv2.FONT_HERSHEY_SIMPLEX,
                        st.text_scale, (0, 0, 0), max(1, st.box_thickness + 1), cv2.LINE_AA)
        if st.text_bg_alpha > 0:
            cv2.addWeighted(overlay, st.text_bg_alpha, image, 1 - st.text_bg_alpha, 0, image)
        for p1, _p2, color, text in entries:
            org = (p1[0], max(st.text_scale * 22, p1[1] - 4))
            cv2.putText(image, text, org, cv2.FONT_HERSHEY_SIMPLEX,
                        st.text_scale, color, 1, cv2.LINE_AA)

    # ------------------------------------------------------------------
    def _draw_labels_pil(
        self,
        image: np.ndarray,
        entries: Sequence[Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int], str]],
        st: Any,
    ) -> np.ndarray:
        """含中文: 整帧转 PIL 绘字 (含半透明背景) 再转回 BGR."""
        from PIL import Image, ImageDraw, ImageFont

        font = self._get_pil_font(st)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        overlay = Image.new("RGBA", pil.size, (0, 0, 0, 0))
        draw_o = ImageDraw.Draw(overlay)
        draw_t = ImageDraw.Draw(pil)

        for p1, _p2, color, text in entries:
            x, y = p1
            if font is not None:
                bbox = draw_t.textbbox((0, 0), text, font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            else:
                tw, th = int(len(text) * 8 * st.text_scale), int(16 * st.text_scale)
            # 标签贴框上沿, 超出图像顶就贴框内
            ty = y - th - 6 if y - th - 6 >= 0 else y + 2
            b, g, r = color
            if st.text_bg_alpha > 0:
                draw_o.rectangle(
                    [x, ty - 2, x + tw + 6, ty + th + 4],
                    fill=(0, 0, 0, int(255 * st.text_bg_alpha)),
                )
            draw_t.text((x + 3, ty), text, font=font, fill=(r, g, b))

        if st.text_bg_alpha > 0:
            pil = Image.alpha_composite(pil.convert("RGBA"), overlay)
        return cv2.cvtColor(np.asarray(pil.convert("RGB")), cv2.COLOR_RGB2BGR)

    # ------------------------------------------------------------------
    def _get_pil_font(self, st: Any) -> Any:
        """懒加载 PIL 字体: font_path → Windows 默认中文字体 → PIL 默认 (中文乱码)."""
        if self._font is not None or self._font_failed:
            return self._font
        from PIL import ImageFont

        candidates: List[str] = []
        if self.font_path:
            candidates.append(self.font_path)
        candidates += [
            "C:/Windows/Fonts/msyh.ttc",     # Windows 微软雅黑
            "/System/Library/Fonts/PingFang.ttc",  # macOS
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux
        ]
        size = max(12, int(st.text_scale * 28))
        for path in candidates:
            try:
                if Path(path).is_file():
                    self._font = ImageFont.truetype(path, size)
                    break
            except OSError:
                continue
        if self._font is None:
            self._font = ImageFont.load_default()
            self._font_failed = True
            logger.warning("未找到中文字体, 中文标签可能显示为方块 (可在 yaml 配 font_path).")
        return self._font
