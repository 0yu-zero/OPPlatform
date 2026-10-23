#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : config_log.py
# @Project   : ODPlatform / common
# @Function  : 配置日志门面 —— 生效配置表 + 覆盖链表 (薄封装 runtime_config.report)
"""
D7 推理 service 用的两个日志函数. 真正的渲染逻辑在 D5 的 runtime_config/report.py,
这里只做门面 (函数内延迟 import, 避免 common 层反向依赖 runtime_config).
"""
from __future__ import annotations

import logging
from typing import Any, Optional


def log_effective_config(config: Any, merger: Any, *, logger: Optional[logging.Logger] = None) -> None:
    """打印生效配置表 (defaults ← yaml ← cli 三方合并后的最终值)."""
    from od_platform.runtime_config.report import render_effective

    log = logger or logging.getLogger(__name__)
    for line in render_effective(config, merger):
        log.info(line)


def log_override_chains(config: Any, merger: Any, *, logger: Optional[logging.Logger] = None) -> None:
    """打印覆盖链表 (每个非默认值是谁覆盖了谁)."""
    from od_platform.runtime_config.report import render_overrides

    log = logger or logging.getLogger(__name__)
    for line in render_overrides(config, merger):
        log.info(line)
