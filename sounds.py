"""
sounds.py - 小铁皮的音效模块
使用 macOS 系统命令 afplay 播放音效
"""

import subprocess
import threading
from pathlib import Path
from typing import Optional

# 系统音效路径
SYSTEM_SOUNDS = Path('/System/Library/Sounds')

# 音效映射
SOUND_EFFECTS = {
    'feed': SYSTEM_SOUNDS / 'Pop.aiff',
    'bath': SYSTEM_SOUNDS / 'Submarine.aiff',
    'play': SYSTEM_SOUNDS / 'Funk.aiff',
    'happy': SYSTEM_SOUNDS / 'Hero.aiff',
    'click': SYSTEM_SOUNDS / 'Tink.aiff',
}

# 音量控制（0.0 - 1.0）
_volume = 0.5
_enabled = True


def set_volume(vol: float) -> None:
    """设置音量 (0.0 - 1.0)"""
    global _volume
    _volume = max(0.0, min(1.0, vol))


def set_enabled(enabled: bool) -> None:
    """启用/禁用音效"""
    global _enabled
    _enabled = enabled


def is_enabled() -> bool:
    """获取音效启用状态"""
    return _enabled


def play(sound_name: str) -> None:
    """播放指定音效"""
    if not _enabled:
        return

    sound_file = SOUND_EFFECTS.get(sound_name)
    if not sound_file or not sound_file.exists():
        return

    def _play():
        try:
            subprocess.run(
                ['afplay', '-v', str(_volume), str(sound_file)],
                check=False,
                capture_output=True
            )
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()


def play_file(file_path: str) -> None:
    """播放指定文件"""
    if not _enabled:
        return

    path = Path(file_path)
    if not path.exists():
        return

    def _play():
        try:
            subprocess.run(
                ['afplay', '-v', str(_volume), str(path)],
                check=False,
                capture_output=True
            )
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()
