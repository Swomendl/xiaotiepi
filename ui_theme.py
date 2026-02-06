"""
ui_theme.py - 小铁皮统一视觉风格
背包、学术日报等弹窗共享的配色和组件
"""

import tkinter as tk
from typing import Optional, Callable

# ═══════════════════════════════════════════════════════════════
#  共享窗口主题配置
# ═══════════════════════════════════════════════════════════════

WINDOW_THEME = {
    # 配色
    'bg_primary': '#FAF0E4',       # 奶油色主背景
    'bg_card': '#FDF8F0',          # 卡片/分区背景
    'bg_card_hover': '#FFF3E0',    # 卡片悬停/选中
    'bg_card_inner': '#FFF9F0',    # 内部元素背景

    'border_primary': '#C4956A',   # 主要边框（棕色）
    'border_light': '#E8D8C4',     # 次要边框/分割线
    'border_dashed': '#D4C4B0',    # 虚线边框

    'text_title': '#FFF9F0',       # 标题栏文字（白）
    'text_primary': '#5C3D2E',     # 主要文字（深棕）
    'text_secondary': '#A0896C',   # 次要文字
    'text_muted': '#D4C4B0',       # 弱化文字
    'text_label': '#A0522D',       # 标签文字

    'title_bar_bg': '#A0522D',     # 标题栏背景（深棕）
    'title_bar_border': '#7A4A2A', # 标题栏底部边框

    # 按钮（像素凸起风格）
    'btn_primary_bg': '#A0522D',
    'btn_primary_highlight': '#D4B896',
    'btn_primary_shadow': '#7A4A2A',
    'btn_secondary_bg': '#C4956A',

    # 分区框样式
    'section_border': '#C4956A',   # fieldset 边框
    'section_label_color': '#A0522D',  # legend 文字
}

# 稀有度颜色
RARITY_THEME = {
    'common': '#8B7355',      # 普通 - 灰棕
    'uncommon': '#4ADE80',    # 优秀 - 绿
    'rare': '#60A5FA',        # 稀有 - 蓝
    'epic': '#A855F7',        # 史诗 - 紫
    'legendary': '#F59E0B',   # 传说 - 金
}


# ═══════════════════════════════════════════════════════════════
#  统一组件
# ═══════════════════════════════════════════════════════════════

def create_section_frame(parent, label: str, **kwargs) -> tk.LabelFrame:
    """
    创建统一风格的分区框
    视觉效果类似 HTML fieldset + legend
    """
    theme = WINDOW_THEME
    frame = tk.LabelFrame(
        parent,
        text=f" {label} ",
        bg=theme['bg_card'],
        fg=theme['section_label_color'],
        font=('Arial', 9, 'bold'),
        bd=2,
        relief='groove',
        padx=8, pady=6,
        **kwargs
    )
    return frame


def create_pixel_button(parent, text: str, command: Callable,
                       primary: bool = False, width: int = 10) -> tk.Button:
    """
    像素凸起风格按钮
    """
    theme = WINDOW_THEME
    bg = theme['btn_primary_bg'] if primary else theme['btn_secondary_bg']

    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=theme['text_title'],
        font=('Arial', 9, 'bold'),
        bd=2,
        relief='raised',
        activebackground=theme['title_bar_border'],
        activeforeground=theme['text_title'],
        width=width,
        cursor='hand2',
    )
    return btn


def create_title_bar(window: tk.Toplevel, title: str,
                    right_text: str = "", right_color: str = None) -> tk.Frame:
    """
    创建统一的标题栏
    """
    theme = WINDOW_THEME

    bar = tk.Frame(window, bg=theme['title_bar_bg'], height=36)
    bar.pack(fill='x')
    bar.pack_propagate(False)

    # 左侧标题
    tk.Label(bar, text=title, font=('Arial', 12, 'bold'),
            bg=theme['title_bar_bg'], fg=theme['text_title']).pack(side='left', padx=12, pady=6)

    # 右侧文字（如等级）
    if right_text:
        color = right_color or theme['text_title']
        tk.Label(bar, text=right_text, font=('Arial', 10),
                bg=theme['title_bar_bg'], fg=color).pack(side='right', padx=12, pady=6)

    return bar


def draw_pixel_lock(canvas: tk.Canvas, x: int, y: int, scale: int = 3) -> None:
    """绘制像素风锁头图标"""
    # 锁扣（U形）
    lock_shackle = [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
    ]
    # 锁身
    lock_body = [
        [1, 1, 1, 1, 1],
        [1, 2, 2, 2, 1],
        [1, 2, 3, 2, 1],
        [1, 2, 2, 2, 1],
        [1, 1, 1, 1, 1],
    ]
    lock_colors = {1: '#A0522D', 2: '#8B5E3C', 3: '#D4880F'}
    shackle_color = '#C4956A'

    # 画锁扣
    for ry, row in enumerate(lock_shackle):
        for rx, c in enumerate(row):
            if c:
                px, py = x + rx * scale, y + ry * scale
                canvas.create_rectangle(px, py, px+scale, py+scale,
                    fill=shackle_color, outline='')

    # 画锁身
    body_y = y + len(lock_shackle) * scale
    for ry, row in enumerate(lock_body):
        for rx, c in enumerate(row):
            if c:
                px, py = x + rx * scale, body_y + ry * scale
                canvas.create_rectangle(px, py, px+scale, py+scale,
                    fill=lock_colors[c], outline='')


def setup_window_style(window: tk.Toplevel, width: int = 420, height: int = 520) -> None:
    """
    设置窗口的统一样式
    """
    theme = WINDOW_THEME
    window.geometry(f"{width}x{height}")
    window.configure(bg=theme['bg_primary'])
    window.resizable(False, False)
