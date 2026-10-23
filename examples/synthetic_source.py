# ── 文件: examples/synthetic_source.py(在 frame_source 之外!)──
import numpy as np
from od_platform.frame_source import (
    FrameSource, SourceConfig, register_source,
    Frame, FrameInfo, create_frame_source, list_sources,
)


class SyntheticConfig(SourceConfig):
    """合成源配置。纯内存, 没有路径 —— 无法用字符串表达, 只能显式传 config。"""
    n_frames: int = 30
    width:    int = 640
    height:   int = 480

    @property
    def identity(self) -> str:
        return f"synthetic:{self.n_frames}帧"


@register_source(SyntheticConfig)     # ← 无 str_matcher: config-only, 和硬件源一样只能显式选型
class SyntheticSource(FrameSource):
    """每帧现生成一张渐变测试图的内存源。"""

    def __init__(self, config: SyntheticConfig):
        super().__init__(config)
        self._n, self._w, self._h = config.n_frames, config.width, config.height
        self._i = 0

    def open(self) -> bool:
        self._i = 0
        self._frame_index = 0
        return True

    def read(self):
        if self._i >= self._n:
            return None
        img = np.full((self._h, self._w, 3), (self._i * 8) % 256, dtype=np.uint8)
        info = FrameInfo(
            width=self._w, height=self._h,
            source_type="synthetic",              # ← 第三方类型字符串(不是内置枚举成员)
            source_path=self.source_path,
            frame_index=self._i, total_frames=self._n,
            filename=f"synthetic_{self._i:04d}",
        )
        self._i += 1
        self._frame_index = self._i
        return Frame(image=img, info=info)

    def close(self) -> None:
        pass

    def get_source_type(self):
        return "synthetic"                        # ← 返回字符串(因为不是内置枚举, §2.1 的放宽在此兑现)
