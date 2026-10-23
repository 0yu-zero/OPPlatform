#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : fill_demo_images.py
# @Project   : ODPlatform
# @Function  : 把 demo 的 0 字节占位图填充为真实可读的小图(D6 真机训练用)
"""D1-D5 全流程只流转【文件名与标签内容】, 不读像素 —— 所以 make_demo.py 故意
生成 0 字节空图(省磁盘、跑得快, 见其注释"空图:全流程不读像素")。

D6 真机训练时 ultralytics 必须真正解码像素, 空图全部被判 corrupt →
"train: No labels found"。本脚本把 raw/demo 的空图就地填充为 64x64 真实 JPG
(随机底色 + 随机矩形, 不改文件名)。

填充后数据内容变了 → sha256 变 → data_fingerprint 变 → 旧流转卡目录自动失效,
D3/D4 需重跑重新盖章 —— 这正是流转卡"数据一变指纹变"白捡失效机制的现场演示。

用法:  python scripts/demo_data/fill_demo_images.py
"""
from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]      # 仓库根
IMG_DIR = ROOT / "data" / "raw" / "demo" / "images"

SIZE = (64, 64)          # 小图: 训练快, 演示够用


def fill_one(path: Path, rng: random.Random) -> bool:
    """把单张 0 字节图填充为真实 JPG。返回是否真的填充了。"""
    if path.stat().st_size > 0:
        return False
    base = (rng.randint(40, 200), rng.randint(40, 200), rng.randint(40, 200))
    im = Image.new("RGB", SIZE, base)
    draw = ImageDraw.Draw(im)
    for _ in range(rng.randint(2, 5)):           # 随机矩形, 模拟目标区域
        x0, y0 = rng.randint(0, SIZE[0] - 10), rng.randint(0, SIZE[1] - 10)
        x1 = min(x0 + rng.randint(6, 24), SIZE[0] - 1)
        y1 = min(y0 + rng.randint(6, 24), SIZE[1] - 1)
        draw.rectangle([x0, y0, x1, y1],
                       fill=(rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255)))
    im.save(path, format="JPEG", quality=85)
    return True


def main() -> None:
    rng = random.Random(42)                      # 固定种子: 填充结果可复现
    images = sorted(p for p in IMG_DIR.iterdir() if p.suffix.lower() == ".jpg")
    filled = sum(1 for p in images if fill_one(p, rng))
    print(f"共 {len(images)} 张, 本次填充 {filled} 张空图 -> {IMG_DIR}")


if __name__ == "__main__":
    main()
