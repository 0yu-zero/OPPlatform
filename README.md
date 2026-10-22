# ODPlatform

通用目标检测开发平台 —— 工程骨架 + 数据层。

## 结构

- `apps/platform/` — 训练 + 离线推理引擎（今天唯一的端）
- `apps/web-backend/`、`apps/desktop/` — 未来端的占位
- `data/`、`models/`、`runs/` — 共享数据 / 权重 / 运行现场
- `docs/` — 设计文档与 ADR

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ./apps/platform
odp-init
```

## 开发期（未装包）入口

```bash
python scripts/init_project.py
```