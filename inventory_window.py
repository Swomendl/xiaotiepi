"""
inventory_window.py - 小铁皮的背包窗口
使用与学术日报统一的暖色像素风格
"""

import tkinter as tk
from typing import Optional, Callable
from items import (
    ITEMS, ITEM_COLORS, ItemSlot,
    get_item, get_item_name, get_unlock_description,
    RARITY_COLORS, RARITY_NAMES, should_show_items
)
from sprites import PIXEL_SIZE, get_all_colors
from ui_theme import (
    WINDOW_THEME, RARITY_THEME,
    create_section_frame, create_pixel_button, create_title_bar,
    draw_pixel_lock, setup_window_style
)


class InventoryWindow:
    """背包窗口 - 暖色像素风格"""

    def __init__(self, root: tk.Tk, save_manager, on_close: Optional[Callable] = None):
        self.root = root
        self.save_manager = save_manager
        self.on_close = on_close
        self.window: Optional[tk.Toplevel] = None
        self.selected_item: Optional[str] = None

        # 槽位中文名
        self.slot_names = {
            'head': '头部',
            'face': '脸部',
            'neck': '脖子',
            'hand': '手持',
            'effect': '特效',
        }

    def show(self) -> None:
        """显示背包窗口"""
        if self.window is not None:
            self.window.lift()
            return

        self.window = tk.Toplevel(self.root)
        self.window.title("小铁皮的背包")
        setup_window_style(self.window, 440, 540)

        # 关闭时的处理
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)

        self._build_ui()

    def _build_ui(self) -> None:
        """构建UI"""
        theme = WINDOW_THEME

        # 标题栏
        level = self.save_manager.get_level()
        stage = self.save_manager.get_level_stage()
        create_title_bar(self.window, "小铁皮的背包",
                        f"Lv.{level} {stage['title']}", stage['color'])

        # 主内容区
        main_frame = tk.Frame(self.window, bg=theme['bg_primary'])
        main_frame.pack(fill='both', expand=True, padx=12, pady=10)

        # 上半部分：预览 + 已装备
        top_frame = tk.Frame(main_frame, bg=theme['bg_primary'])
        top_frame.pack(fill='x', pady=(0, 8))

        # 预览区
        preview_section = create_section_frame(top_frame, "预览", width=110, height=100)
        preview_section.pack(side='left', padx=(0, 10), fill='y')
        preview_section.pack_propagate(False)

        self.preview_canvas = tk.Canvas(preview_section, width=90, height=75,
                                        bg=theme['bg_card_inner'], highlightthickness=1,
                                        highlightbackground=theme['border_light'])
        self.preview_canvas.pack(pady=5)
        self._draw_preview()

        # 已装备区
        equipped_section = create_section_frame(top_frame, "已装备")
        equipped_section.pack(side='left', fill='both', expand=True)

        self.equipped_labels = {}
        equipped = self.save_manager.get_equipped_items()

        for slot in ['head', 'face', 'neck', 'effect']:
            row = tk.Frame(equipped_section, bg=theme['bg_card'])
            row.pack(fill='x', padx=2, pady=1)

            tk.Label(row, text=f"{self.slot_names[slot]} ▸",
                    font=('Arial', 9), bg=theme['bg_card'],
                    fg=theme['text_secondary'], width=6, anchor='e').pack(side='left')

            item_id = equipped.get(slot)
            item_name = get_item_name(item_id) if item_id else "(空)"
            color = theme['text_primary'] if item_id else theme['text_muted']

            lbl = tk.Label(row, text=item_name, font=('Arial', 9),
                          bg=theme['bg_card'], fg=color, cursor='hand2')
            lbl.pack(side='left', padx=5)
            lbl.bind('<Button-1>', lambda e, s=slot: self._on_equipped_click(s))
            self.equipped_labels[slot] = lbl

        # 道具计数
        inv = self.save_manager.get_inventory()
        owned_count = len(inv['owned_items'])
        total_count = len(ITEMS)
        tk.Label(equipped_section, text=f"◈ {owned_count}/{total_count} 件道具",
                font=('Arial', 8), bg=theme['bg_card'],
                fg=theme['text_secondary']).pack(anchor='w', pady=(5, 0))

        # 道具栏
        items_section = create_section_frame(main_frame, "道具栏", height=150)
        items_section.pack(fill='x', pady=(0, 8))
        items_section.pack_propagate(False)

        self.items_canvas = tk.Canvas(items_section, bg=theme['bg_card_inner'],
                                      highlightthickness=0, height=120)
        self.items_canvas.pack(fill='both', expand=True, padx=2, pady=2)
        self.items_canvas.bind('<Button-1>', self._on_item_click)

        self._draw_items()

        # 详情区
        detail_section = create_section_frame(main_frame, "详情", height=140)
        detail_section.pack(fill='x')
        detail_section.pack_propagate(False)

        detail_inner = tk.Frame(detail_section, bg=theme['bg_card'])
        detail_inner.pack(fill='both', expand=True)

        # 左侧：道具预览
        self.detail_preview = tk.Canvas(detail_inner, width=50, height=50,
                                        bg=theme['bg_card_inner'],
                                        highlightthickness=1,
                                        highlightbackground=theme['border_light'])
        self.detail_preview.pack(side='left', padx=(5, 10), pady=5)

        # 右侧：文字信息
        detail_text = tk.Frame(detail_inner, bg=theme['bg_card'])
        detail_text.pack(side='left', fill='both', expand=True, pady=5)

        self.detail_name = tk.Label(detail_text, text="选择一个道具",
                                   font=('Arial', 11, 'bold'), bg=theme['bg_card'],
                                   fg=theme['text_muted'], anchor='w')
        self.detail_name.pack(fill='x')

        self.detail_rarity = tk.Label(detail_text, text="",
                                     font=('Arial', 8), bg=theme['bg_card'],
                                     fg=theme['text_secondary'], anchor='w')
        self.detail_rarity.pack(fill='x')

        # 分割线
        tk.Frame(detail_text, bg=theme['border_light'], height=1).pack(fill='x', pady=3)

        self.detail_desc = tk.Label(detail_text, text="",
                                   font=('Arial', 9), bg=theme['bg_card'],
                                   fg=theme['text_primary'], anchor='w',
                                   wraplength=280, justify='left')
        self.detail_desc.pack(fill='x')

        # 按钮区
        btn_frame = tk.Frame(detail_text, bg=theme['bg_card'])
        btn_frame.pack(fill='x', pady=(8, 0))

        self.equip_btn = create_pixel_button(btn_frame, "装 备",
                                             self._equip_selected, primary=True, width=8)
        self.equip_btn.pack(side='left', padx=(0, 8))
        self.equip_btn.config(state='disabled')

        self.unequip_btn = create_pixel_button(btn_frame, "卸 下",
                                               self._unequip_selected, primary=False, width=8)
        self.unequip_btn.pack(side='left')
        self.unequip_btn.config(state='disabled')

    def _draw_preview(self) -> None:
        """绘制预览（简化版小铁皮 + 道具）"""
        self.preview_canvas.delete('all')
        theme = WINDOW_THEME

        # 简化的小铁皮轮廓
        ps = 5  # 预览用的像素大小
        ox, oy = 22, 12

        # 身体轮廓（简化）
        body_color = '#D4856A'
        outline_color = '#8B5A4A'

        # 画简化的身体
        for r in range(7):
            for c in range(8):
                if r == 0 and (c < 2 or c > 5):
                    continue
                if r == 6 and (c == 0 or c == 7):
                    continue
                x = ox + c * ps
                y = oy + r * ps
                self.preview_canvas.create_rectangle(x, y, x+ps, y+ps,
                                                     fill=body_color, outline=outline_color)

        # 画眼睛
        eye_color = '#1A1A1A'
        self.preview_canvas.create_rectangle(ox+2*ps, oy+2*ps, ox+3*ps, oy+3*ps,
                                             fill=eye_color, outline='')
        self.preview_canvas.create_rectangle(ox+5*ps, oy+2*ps, ox+6*ps, oy+3*ps,
                                             fill=eye_color, outline='')

        # 画装备的道具（简化显示）
        equipped = self.save_manager.get_equipped_items()
        colors = get_all_colors(50)

        for slot in ['neck', 'face', 'head']:
            item_id = equipped.get(slot)
            if not item_id:
                continue
            item = ITEMS.get(item_id)
            if not item or not item.get('sprite'):
                continue

            sprite = item['sprite']
            offset = item.get('offset', (0, 0))

            # 缩放绘制道具
            for r, row in enumerate(sprite):
                for c, val in enumerate(row):
                    if val == 0:
                        continue
                    color = colors.get(val, '#FF00FF')
                    x = ox + (c + offset[0]) * ps
                    y = oy + (r + offset[1]) * ps
                    self.preview_canvas.create_rectangle(x, y, x+ps, y+ps,
                                                         fill=color, outline='')

    def _draw_items(self) -> None:
        """绘制道具栏"""
        self.items_canvas.delete('all')
        self.item_rects = {}
        theme = WINDOW_THEME

        inv = self.save_manager.get_inventory()
        owned = inv['owned_items']
        equipped = inv['equipped']
        equipped_items = set(v for v in equipped.values() if v)

        x, y = 5, 5
        box_size = 52
        gap = 6

        # 已拥有的道具
        for item_id in owned:
            item = ITEMS.get(item_id)
            if not item:
                continue

            rarity = item.get('rarity', 'common')
            rarity_color = RARITY_THEME.get(rarity, theme['text_primary'])

            # 选中高亮
            if item_id == self.selected_item:
                bg_color = theme['bg_card_hover']
                border_width = 2
            else:
                bg_color = theme['bg_card_inner']
                border_width = 1

            # 已装备标记背景
            if item_id in equipped_items:
                bg_color = '#E8F5E9'

            # 绘制道具框
            self.items_canvas.create_rectangle(
                x, y, x + box_size, y + box_size,
                fill=bg_color, outline=rarity_color, width=border_width
            )

            # 绘制道具缩略图
            self._draw_item_thumbnail(item, x + 10, y + 5, scale=3)

            # 道具名（下方）
            self.items_canvas.create_text(
                x + box_size // 2, y + box_size - 8,
                text=item['name'][:4], fill=theme['text_primary'],
                font=('Arial', 7)
            )

            # 已装备标记
            if item_id in equipped_items:
                self.items_canvas.create_text(
                    x + box_size - 8, y + 8,
                    text="E", fill='#4ADE80', font=('Arial', 8, 'bold')
                )

            self.item_rects[item_id] = (x, y, x + box_size, y + box_size)

            x += box_size + gap
            if x > 360:
                x = 5
                y += box_size + gap

        # 未解锁道具（锁定状态）
        for item_id, item in ITEMS.items():
            if item_id in owned:
                continue

            # 绘制锁定框
            self.items_canvas.create_rectangle(
                x, y, x + box_size, y + box_size,
                fill=theme['bg_card'], outline=theme['border_dashed'], width=1
            )

            # 绘制像素锁头
            draw_pixel_lock(self.items_canvas, x + 18, y + 10, scale=2)

            # 问号文字
            self.items_canvas.create_text(
                x + box_size // 2, y + box_size - 8,
                text="???", fill=theme['text_muted'], font=('Arial', 7)
            )

            self.item_rects[f"locked_{item_id}"] = (x, y, x + box_size, y + box_size)

            x += box_size + gap
            if x > 360:
                x = 5
                y += box_size + gap

    def _draw_item_thumbnail(self, item: dict, x: int, y: int, scale: int = 3) -> None:
        """绘制道具缩略图"""
        sprite = item.get('sprite')
        if not sprite:
            return

        colors = get_all_colors(50)
        for r, row in enumerate(sprite):
            for c, val in enumerate(row):
                if val == 0:
                    continue
                color = colors.get(val, '#FF00FF')
                px = x + c * scale
                py = y + r * scale
                self.items_canvas.create_rectangle(px, py, px+scale, py+scale,
                                                   fill=color, outline='')

    def _draw_detail_thumbnail(self, item: dict) -> None:
        """在详情区绘制道具缩略图"""
        self.detail_preview.delete('all')
        sprite = item.get('sprite')
        if not sprite:
            return

        colors = get_all_colors(50)
        scale = 4
        # 居中
        sprite_w = len(sprite[0]) * scale
        sprite_h = len(sprite) * scale
        ox = (50 - sprite_w) // 2
        oy = (50 - sprite_h) // 2

        for r, row in enumerate(sprite):
            for c, val in enumerate(row):
                if val == 0:
                    continue
                color = colors.get(val, '#FF00FF')
                px = ox + c * scale
                py = oy + r * scale
                self.detail_preview.create_rectangle(px, py, px+scale, py+scale,
                                                     fill=color, outline='')

    def _on_item_click(self, event) -> None:
        """道具点击事件"""
        click_x, click_y = event.x, event.y

        for item_id, (x1, y1, x2, y2) in self.item_rects.items():
            if x1 <= click_x <= x2 and y1 <= click_y <= y2:
                if item_id.startswith('locked_'):
                    real_id = item_id.replace('locked_', '')
                    self._show_locked_detail(real_id)
                else:
                    self._select_item(item_id)
                return

    def _on_equipped_click(self, slot: str) -> None:
        """点击已装备栏"""
        equipped = self.save_manager.get_equipped_items()
        item_id = equipped.get(slot)
        if item_id:
            self._select_item(item_id)

    def _select_item(self, item_id: str) -> None:
        """选中道具"""
        self.selected_item = item_id
        self._draw_items()
        self._show_detail(item_id)

    def _show_detail(self, item_id: str) -> None:
        """显示道具详情"""
        theme = WINDOW_THEME
        item = ITEMS.get(item_id)
        if not item:
            return

        rarity = item.get('rarity', 'common')
        rarity_color = RARITY_THEME.get(rarity, theme['text_primary'])
        rarity_name = RARITY_NAMES.get(rarity, '普通')

        self.detail_name.config(text=item['name'], fg=rarity_color)
        self.detail_rarity.config(
            text=f"稀有度: {rarity_name} │ 槽位: {self.slot_names.get(item['slot'], item['slot'])}"
        )
        self.detail_desc.config(text=item.get('description', ''))

        # 绘制缩略图
        self._draw_detail_thumbnail(item)

        # 更新按钮状态
        equipped = self.save_manager.get_equipped_items()
        is_equipped = item_id in equipped.values()

        if is_equipped:
            self.equip_btn.config(state='disabled')
            self.unequip_btn.config(state='normal')
        else:
            self.equip_btn.config(state='normal')
            self.unequip_btn.config(state='disabled')

    def _show_locked_detail(self, item_id: str) -> None:
        """显示未解锁道具详情"""
        theme = WINDOW_THEME
        item = ITEMS.get(item_id)
        if not item:
            return

        self.selected_item = None
        self._draw_items()

        self.detail_name.config(text=f"??? {item['name']}", fg=theme['text_muted'])
        self.detail_rarity.config(text=f"解锁条件: {get_unlock_description(item_id)}")
        self.detail_desc.config(text="尚未解锁...")

        # 在详情预览区画锁
        self.detail_preview.delete('all')
        draw_pixel_lock(self.detail_preview, 15, 10, scale=3)

        self.equip_btn.config(state='disabled')
        self.unequip_btn.config(state='disabled')

    def _equip_selected(self) -> None:
        """装备选中的道具"""
        if not self.selected_item:
            return

        item = ITEMS.get(self.selected_item)
        if not item:
            return

        slot = item['slot']
        self.save_manager.equip_item(self.selected_item, slot)
        self.save_manager.save()

        self._refresh_ui()

    def _unequip_selected(self) -> None:
        """卸下选中的道具"""
        if not self.selected_item:
            return

        item = ITEMS.get(self.selected_item)
        if not item:
            return

        slot = item['slot']
        self.save_manager.unequip_item(slot)
        self.save_manager.save()

        self._refresh_ui()

    def _refresh_ui(self) -> None:
        """刷新整个UI"""
        theme = WINDOW_THEME
        equipped = self.save_manager.get_equipped_items()

        for slot, lbl in self.equipped_labels.items():
            item_id = equipped.get(slot)
            item_name = get_item_name(item_id) if item_id else "(空)"
            color = theme['text_primary'] if item_id else theme['text_muted']
            lbl.config(text=item_name, fg=color)

        self._draw_items()
        self._draw_preview()

        if self.selected_item:
            self._show_detail(self.selected_item)

    def _on_window_close(self) -> None:
        """窗口关闭"""
        if self.on_close:
            self.on_close()
        self.window.destroy()
        self.window = None

    def close(self) -> None:
        """关闭窗口"""
        if self.window:
            self._on_window_close()
