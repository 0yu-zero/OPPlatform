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

重置时清理派生数据、训练运行产物、训练权重和日志（默认会要求确认）：

```bash
odp-reset
```

在自动化场景中可用 `odp-reset --yes` 跳过交互确认。

## 开发期（未装包）入口

```bash
python scripts/init_project.py
```