"""
pet.py - 小铁皮的主逻辑模块
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional
import time
import math
import random

import sprites
import sounds
from sprites import (SPRITES, COLORS, get_canvas_size, get_sprite,
                     get_dynamic_colors, get_all_colors, get_season_accessory,
                     get_current_season, SEASON_COLORS,
                     SPRITE_SHOWER_HEAD, SPRITE_ONIGIRI, SPRITE_PS4_CONTROLLER,
                     SPRITE_DREAM_CLOUD, SPRITE_NIGHTMARE_CLOUD,
                     DREAM_ICONS_GOOD, DREAM_ICONS_BAD, HAPPY_EVENT_SPRITES,
                     ANIMATION_COLORS, SPRITE_PAPER)
from bubble import save_custom_dialogue
from save import SaveManager
from bubble import Bubble, PaperBubbleManager
import threading
from datetime import datetime


class Pet:
    """桌面宠物主类"""

    def __init__(self):
        # 初始化主窗口
        self.root = tk.Tk()
        self.root.title('小铁皮')

        # 无边框透明窗口
        self.root.overrideredirect(True)
        self.root.wm_attributes('-topmost', True)

        # macOS 透明背景
        try:
            self.root.wm_attributes('-transparent', True)
            self.root.config(bg='systemTransparent')
            self._canvas_bg = 'systemTransparent'
        except tk.TclError:
            self._canvas_bg = '#2D2D2D'
            self.root.config(bg=self._canvas_bg)

        # 画布尺寸
        canvas_w, canvas_h = get_canvas_size()

        # 创建画布
        self.canvas = tk.Canvas(
            self.root,
            width=canvas_w,
            height=canvas_h,
            highlightthickness=0,
            bg=self._canvas_bg
        )
        self.canvas.pack()

        # 状态管理
        self.save_manager = SaveManager()
        self.bubble = Bubble(self.root)
        self.paper_bubble = PaperBubbleManager(self.root)

        # 动画状态
        self.current_frame = 0
        self.tick_ms = 50  # 动画刷新间隔
        self.bounce_phase = 0.0  # 呼吸弹跳相位

        # 眨眼
        self.is_blinking = False
        self._blink_job = None

        # 移动状态
        self.is_walking = False
        self.walk_direction = 1  # 1=右, -1=左
        self.walk_speed = 2
        self.walk_frame = 0
        self.walk_tick = 0

        # 跳跃状态
        self.jumping = False
        self.jump_vy = 0.0
        self.jump_y = 0.0
        self.jump_velocity = -10
        self.gravity = 0.8

        # 开心状态计时
        self.happy_timer = 0

        # 拖拽状态
        self.drag_data = {'x': 0, 'y': 0, 'dragging': False}
        self._press_rx = 0
        self._press_ry = 0

        # Zzz 动画状态
        self.zzz_phase = 0.0
        self.zzz_items = []  # 存储 Zzz 文字的位置和透明度

        # 季节特效状态
        self.season_effect_timer = 0
        self.is_sneezing = False  # 冬天打喷嚏
        self.is_sweating = False  # 夏天擦汗
        self.falling_leaves = []  # 秋天落叶 [{x, y, speed}]
        self.falling_petals = []  # 春天花瓣

        # 晕倒系统
        self.is_dizzy = False
        self.dizzy_timer = 0
        self.is_falling = False
        self.fall_velocity = 0
        self.drag_history = []
        self.shake_threshold = 400
        self.direction_changes = 0
        self.shake_count = 0
        self.shake_angry = False
        self.shake_angry_timer = 0
        self.is_hiding = False

        # 洗澡动画状态
        self.is_bathing = False
        self.bath_timer = 0
        self.bath_duration = 100  # 100帧 = 5秒
        self.water_drops = []
        self.shower_offset_y = 0

        # 喂食动画状态
        self.is_eating = False
        self.eat_timer = 0
        self.eat_duration = 80  # 80帧 = 4秒
        self.eat_phase = 0.0
        self.onigiri_offset = 0

        # 玩耍动画状态
        self.is_playing_game = False
        self.play_timer = 0
        self.play_duration = 120
        self.controller_shake = 0.0
        self.button_blink_timer = 0

        # 鼠标追踪
        self.mouse_x = 0
        self.mouse_y = 0
        self.last_mouse_move = time.time()
        self.eye_direction = 'center'

        # 走路模式
        self.walk_mode = 'normal'
        self.walk_pause_timer = 0
        self.is_looking_around = False
        self.look_direction = 'left'
        self.look_count = 0
        self.look_timer = 0

        # 打哈欠
        self.is_yawning = False
        self.yawn_timer = 0

        # 坐下休息
        self.is_sitting = False
        self.sit_timer = 0
        self.foot_swing_phase = 0.0

        # 体型
        self.body_type = self.save_manager.get_body_type()

        # 睡眠打扰状态
        self.sleep_disturb_state = None  # None, 'sleepy', 'annoyed', 'super_annoyed'
        self.sleep_disturb_timer = 0

        # 梦境系统
        self.is_dreaming = False
        self.dream_type = None  # 'good', 'bad', None
        self.dream_timer = 0
        self.dream_icon_index = 0
        self.dream_float_phase = 0.0
        self.last_dream_time = 0

        # 被安慰动画
        self.is_being_comforted = False
        self.comfort_timer = 0

        # 随机开心事件
        self.happy_event_active = False
        self.happy_event_type = None
        self.happy_event_timer = 0
        self.happy_event_pos = [0, 0]
        self.happy_event_phase = 0.0
        self.last_happy_event_check = time.time()

        # 论文阅读系统
        self.is_reading_papers = False
        self.reading_timer = 0
        self.reading_eye_phase = 0
        self.push_glasses_timer = 0
        self.paper_chat_window = None
        self.paper_fetching = False
        self.today_papers = []
        self.paper_briefing_ready = False

        # 大小设置
        self.size_options = {'迷你': 4, '小': 5, '中': 7, '大': 10, '巨大': 14}
        self.current_size_name = '中'

        # 屏幕尺寸
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        # 初始位置（屏幕底部中央）
        sprite_h = 9 * sprites.PIXEL_SIZE
        self.x = self.screen_w // 2
        self.y = self.screen_h - 100 - sprite_h
        self.base_y = self.y
        self.root.geometry(f'+{self.x}+{self.y}')

        # 衰减计时
        self.last_decay_time = time.time()
        self.decay_interval = 60  # 每60秒检查一次衰减

        # 自动保存间隔
        self.save_interval = 30000  # 30秒

        # 绑定事件
        self._bind_events()

        # 创建右键菜单
        self._create_context_menu()

        # 启动循环
        self._schedule_blink()
        self._tick()
        self._decay_loop()
        self._auto_save()
        self._schedule_paper_fetch()

        # 打招呼
        self.root.after(800, lambda: self.bubble.say_random(self.save_manager.get_status()))

    def _bind_events(self) -> None:
        """绑定鼠标事件"""
        self.canvas.bind('<ButtonPress-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)
        self.canvas.bind('<ButtonPress-2>', self._show_menu)  # macOS 右键
        self.canvas.bind('<Control-ButtonPress-1>', self._show_menu)

    def _create_context_menu(self) -> None:
        """创建右键菜单"""
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label='🍙 喂食', command=self._feed)
        self.menu.add_command(label='🛁 洗澡', command=self._bath)
        self.menu.add_command(label='🎮 玩耍', command=self._play)
        self.menu.add_separator()
        self.menu.add_command(label='📊 状态查看', command=self._show_status)
        self.menu.add_command(label='💬 说点什么', command=self._say_something)
        self.menu.add_command(label='🎓 教它说话', command=self._teach_dialogue)
        self.menu.add_command(label='🫂 安慰一下', command=self._comfort)
        self.menu.add_separator()
        self.menu.add_command(label='📰 今日论文', command=self._open_paper_chat)
        self.menu.add_command(label='🔑 设置 API Key', command=self._set_api_key)

        # 走动控制
        self.walk_menu_index = self.menu.index(tk.END) + 1
        self.menu.add_command(label='🚶 走一走', command=self._toggle_walk)

        # 大小调整子菜单
        self.size_menu = tk.Menu(self.menu, tearoff=0)
        for name, size in self.size_options.items():
            self.size_menu.add_command(
                label=name,
                command=lambda n=name, s=size: self._set_size(n, s)
            )
        self.menu.add_cascade(label='📏 大小', menu=self.size_menu)

        self.menu.add_separator()
        self.menu.add_command(label='💀 复活', command=self._revive, state='disabled')
        self.menu.add_command(label='❌ 拜拜', command=self._quit)

    def _show_menu(self, event: tk.Event) -> None:
        """显示右键菜单"""
        # 更新复活菜单项状态
        if self.save_manager.data.get('is_dead'):
            self.menu.entryconfig('💀 复活', state='normal')
        else:
            self.menu.entryconfig('💀 复活', state='disabled')

        # 更新走动菜单文字
        if self.is_walking:
            self.menu.entryconfig(self.walk_menu_index, label='🛑 停下来')
        else:
            self.menu.entryconfig(self.walk_menu_index, label='🚶 走一走')

        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _get_current_sprite(self):
        body_type = self.save_manager.get_body_type()

        if self.is_dizzy or self.is_falling:
            return get_sprite(body_type, 'dizzy')[0]

        if self.save_manager.data.get('is_dead'):
            return get_sprite(body_type, 'dead')[0]

        if self.shake_angry and self.is_hiding:
            sprite = get_sprite(body_type, 'angry')[0]
            return [row[::-1] for row in sprite]

        if self.is_being_comforted:
            return get_sprite(body_type, 'comforted')[0]

        if self.is_reading_papers:
            if self.push_glasses_timer > 0:
                frames = get_sprite(body_type, 'push_glasses')
                idx = 0 if self.push_glasses_timer > 15 else 1
                return frames[idx]
            else:
                frames = get_sprite(body_type, 'reading')
                return frames[self.reading_eye_phase % len(frames)]

        if self.sleep_disturb_state == 'sleepy':
            return get_sprite(body_type, 'sleepy_disturbed')[0]
        elif self.sleep_disturb_state == 'annoyed':
            return get_sprite(body_type, 'annoyed_sleepy')[0]
        elif self.sleep_disturb_state == 'super_annoyed':
            return get_sprite(body_type, 'super_annoyed')[0]

        if self.is_yawning:
            return get_sprite(body_type, 'yawn')[0]

        if self.is_sitting:
            return get_sprite(body_type, 'sit')[0]

        if self.happy_timer > 0:
            return get_sprite(body_type, 'happy')[0]

        if self.is_blinking:
            return get_sprite(body_type, 'idle')[1]

        if self.is_looking_around:
            return get_sprite(body_type, f'look_{self.look_direction}')[0]

        if self.is_walking:
            if self.walk_mode == 'run':
                frames = get_sprite(body_type, 'run')
            elif self.walk_mode == 'hop':
                frames = get_sprite(body_type, 'hop')
            else:
                frames = get_sprite(body_type, 'walk')
            return frames[self.walk_frame % len(frames)]

        status = self.save_manager.get_status()
        frames = get_sprite(body_type, status)
        return frames[0]

    def _draw(self) -> None:
        """绘制当前精灵图"""
        self.canvas.delete('all')

        sprite = self._get_current_sprite()
        ps = sprites.PIXEL_SIZE
        pad = ps * 2

        # 获取动态颜色（根据活力值），包含季节配件色
        vitality = self.save_manager.get_vitality()
        colors = get_all_colors(vitality)

        if self.jumping:
            oy = int(self.jump_y)
        elif self.is_sitting:
            oy = 0
        elif not self.is_walking and self.happy_timer <= 0:
            oy = int(math.sin(self.bounce_phase) * 2.5)
        else:
            oy = 0

        foot_swing = 0
        if self.is_sitting:
            foot_swing = int(math.sin(self.foot_swing_phase) * 3)

        # 获取当前状态
        status = self.save_manager.get_status()

        # 如果朝左，翻转精灵图
        flip = self.walk_direction == -1
        if flip:
            sprite = [row[::-1] for row in sprite]

        for r, row in enumerate(sprite):
            for c, val in enumerate(row):
                if val == 0:
                    continue
                color = colors.get(val, '#D4856A')
                x1 = pad + c * ps
                y1 = pad + r * ps + oy
                if self.is_sitting and r >= 7:
                    x1 += foot_swing
                self.canvas.create_rectangle(
                    x1, y1, x1 + ps, y1 + ps,
                    fill=color, outline=color
                )

        # 绘制季节配件（睡觉时不显示）
        if status != 'sleep' and status != 'dead':
            accessory = get_season_accessory()
            if accessory:
                acc = [row[::-1] for row in accessory] if flip else accessory
                for r, row in enumerate(acc):
                    for c, val in enumerate(row):
                        if val == 0:
                            continue
                        color = colors.get(val, '#FFFFFF')
                        x1 = pad + c * ps
                        y1 = pad + r * ps + oy
                        self.canvas.create_rectangle(
                            x1, y1, x1 + ps, y1 + ps,
                            fill=color, outline=color
                        )

        # 绘制 Zzz 动画（睡觉时）
        if status == 'sleep':
            self._draw_zzz(pad, oy)

        # 绘制晕倒星星
        if self.is_dizzy or self.is_falling:
            self._draw_dizzy_stars(pad, oy)

        # 绘制季节特效
        self._draw_season_effects(pad, oy)

        # 绘制动作动画
        self._draw_bath(pad, oy)
        self._draw_eating(pad, oy)
        self._draw_playing(pad, oy)
        self._draw_dream(pad, oy)
        self._draw_happy_event(pad, oy)
        self._draw_paper(pad, oy)

    def _draw_dizzy_stars(self, pad: int, oy: int) -> None:
        """绘制晕倒时头顶转圈的像素星星"""
        ps = sprites.PIXEL_SIZE
        center_x = pad + 5 * ps
        center_y = pad + 1 * ps + oy

        # 星星转圈
        phase = time.time() * 5  # 旋转速度
        for i in range(3):
            angle = phase + i * (2 * math.pi / 3)
            star_x = center_x + math.cos(angle) * 18
            star_y = center_y + math.sin(angle) * 10

            # 绘制像素星星（小十字形）
            size = 2
            color = '#FFD700'  # 金色
            # 中心
            self.canvas.create_rectangle(
                star_x - size, star_y - size,
                star_x + size, star_y + size,
                fill=color, outline=color
            )
            # 四个角
            for dx, dy in [(-size*2, 0), (size*2, 0), (0, -size*2), (0, size*2)]:
                self.canvas.create_rectangle(
                    star_x + dx - 1, star_y + dy - 1,
                    star_x + dx + 1, star_y + dy + 1,
                    fill=color, outline=color
                )

    def _draw_zzz(self, pad: int, oy: int) -> None:
        """绘制 Zzz 飘动动画"""
        ps = sprites.PIXEL_SIZE

        # 更新 Zzz 相位
        self.zzz_phase += 0.15

        # 计算 Zzz 位置（从右上角飘出）
        base_x = pad + 8 * ps
        base_y = pad + oy

        # 三个 Z，依次飘出
        for i, size in enumerate([8, 10, 12]):
            # 每个 Z 有不同的相位偏移
            phase = self.zzz_phase - i * 1.5
            if phase < 0:
                continue

            # 计算位置（向右上飘动）
            float_y = base_y - int(phase * 3) % 40
            float_x = base_x + int(phase * 1.5) % 20 + i * 8

            # 透明度（越高越淡）- 用颜色深浅模拟
            alpha = max(0.3, 1 - (phase % 8) / 8)

            # 根据 alpha 调整颜色
            gray = int(128 + 127 * (1 - alpha))
            color = f'#{gray:02x}{gray:02x}{gray:02x}'

            self.canvas.create_text(
                float_x, float_y,
                text='z',
                font=('Arial', size, 'bold'),
                fill=color
            )

    def _draw_season_effects(self, pad: int, oy: int) -> None:
        """绘制季节特效（像素风格）"""
        season = get_current_season()
        ps = sprites.PIXEL_SIZE

        # 秋天落叶（像素小方块）
        if season == 'autumn':
            for leaf in self.falling_leaves:
                # 橙色/棕色像素叶子
                color = '#D2691E' if leaf.get('type', 0) == 0 else '#CD853F'
                size = 3
                x, y = leaf['x'], leaf['y']
                self.canvas.create_rectangle(
                    x, y, x + size, y + size,
                    fill=color, outline=color
                )
                self.canvas.create_rectangle(
                    x + size, y + size, x + size * 2, y + size * 2,
                    fill=color, outline=color
                )

        # 春天花瓣（像素粉色点）
        elif season == 'spring':
            for petal in self.falling_petals:
                size = 3
                self.canvas.create_rectangle(
                    petal['x'], petal['y'],
                    petal['x'] + size, petal['y'] + size,
                    fill='#FFB6C1', outline='#FFB6C1'
                )

        # 冬天打喷嚏效果（像素气流）
        if self.is_sneezing:
            base_x = pad + 10 * ps
            base_y = pad + 5 * ps + oy
            # 三个递减的像素点表示气流
            for i, offset in enumerate([0, 5, 9]):
                size = 3 - i
                self.canvas.create_rectangle(
                    base_x + offset, base_y - i,
                    base_x + offset + size, base_y - i + size,
                    fill='#ADD8E6', outline='#ADD8E6'
                )

        # 夏天擦汗效果（像素汗珠）
        if self.is_sweating:
            base_x = pad + 1 * ps
            base_y = pad + 3 * ps + oy
            # 蓝色像素汗珠
            self.canvas.create_rectangle(
                base_x, base_y, base_x + 2, base_y + 3,
                fill='#87CEEB', outline='#87CEEB'
            )
            self.canvas.create_rectangle(
                base_x, base_y + 4, base_x + 2, base_y + 6,
                fill='#87CEEB', outline='#87CEEB'
            )

    def _update_season_effects(self) -> None:
        """更新季节特效"""
        season = get_current_season()
        ps = sprites.PIXEL_SIZE
        canvas_w, canvas_h = get_canvas_size()

        # 秋天落叶
        if season == 'autumn':
            # 随机添加新落叶
            if random.random() < 0.03 and len(self.falling_leaves) < 5:
                self.falling_leaves.append({
                    'x': random.randint(0, canvas_w),
                    'y': -10,
                    'speed': random.uniform(0.5, 1.5),
                    'type': random.randint(0, 1)  # 不同颜色
                })

            # 更新落叶位置
            for leaf in self.falling_leaves:
                leaf['y'] += leaf['speed']
                leaf['x'] += math.sin(leaf['y'] / 10) * 0.5

            # 移除超出范围的落叶
            self.falling_leaves = [l for l in self.falling_leaves if l['y'] < canvas_h + 10]

        # 春天花瓣
        elif season == 'spring':
            if random.random() < 0.02 and len(self.falling_petals) < 3:
                self.falling_petals.append({
                    'x': random.randint(0, canvas_w),
                    'y': -5,
                    'speed': random.uniform(0.3, 0.8)
                })

            for petal in self.falling_petals:
                petal['y'] += petal['speed']
                petal['x'] += math.sin(petal['y'] / 8) * 0.3

            self.falling_petals = [p for p in self.falling_petals if p['y'] < canvas_h + 5]

        # 季节特效计时器
        self.season_effect_timer += 1

        # 冬天偶尔打喷嚏
        if season == 'winter':
            if self.is_sneezing:
                if self.season_effect_timer % 20 == 0:
                    self.is_sneezing = False
            elif random.random() < 0.002:  # 偶尔打喷嚏
                self.is_sneezing = True

        # 夏天偶尔擦汗
        elif season == 'summer':
            if self.is_sweating:
                if self.season_effect_timer % 30 == 0:
                    self.is_sweating = False
            elif random.random() < 0.002:  # 偶尔擦汗
                self.is_sweating = True

    def _tick(self) -> None:
        self._update_dizzy()
        self._update_falling()
        self._update_season_effects()
        self._update_bath()
        self._update_eating()
        self._update_playing()
        self._update_dream()
        self._update_sleep_disturb()
        self._update_comfort()
        self._update_happy_event()
        self._update_reading()

        if self.is_dizzy or self.is_falling:
            self._draw()
            self.root.after(self.tick_ms, self._tick)
            return

        self._update_mouse_tracking()
        self._update_behaviors()
        self._check_random_happy_event()

        if self.is_walking and not self.save_manager.data.get('is_dead'):
            self._update_walking()

        if self.is_sitting:
            self.foot_swing_phase += 0.15

        if not self.is_walking and not self.jumping and not self.is_sitting:
            self.bounce_phase += 0.08

        if self.jumping:
            self.jump_vy += self.gravity
            self.jump_y += self.jump_vy
            if self.jump_y >= 0:
                self.jump_y = 0
                self.jumping = False

        if self.happy_timer > 0:
            self.happy_timer -= 1

        self._draw()
        self.root.after(self.tick_ms, self._tick)

    def _schedule_blink(self) -> None:
        """安排眨眼"""
        if self._blink_job:
            self.root.after_cancel(self._blink_job)
        delay = random.randint(2000, 6000)
        self._blink_job = self.root.after(delay, self._blink)

    def _blink(self) -> None:
        """眨眼"""
        self.is_blinking = True
        self.root.after(150, self._unblink)

    def _unblink(self) -> None:
        """眨眼结束"""
        self.is_blinking = False
        self._schedule_blink()

    def _update_mouse_tracking(self) -> None:
        self.eye_direction = 'center'

    def _update_behaviors(self) -> None:
        now = time.time()
        idle_time = now - self.last_mouse_move

        if self.shake_angry_timer > 0:
            self.shake_angry_timer -= 1
            if self.shake_angry_timer <= 0:
                self.shake_angry = False
                self.shake_count = 0
                self.is_hiding = False

        if self.shake_angry and not self.is_hiding:
            if self.x > self.screen_w // 2:
                target_x = self.screen_w - 50
            else:
                target_x = 10
            if abs(self.x - target_x) > 5:
                self.x += 8 if target_x > self.x else -8
                self.root.geometry(f'+{self.x}+{self.y}')
            else:
                self.is_hiding = True

        if self.is_yawning:
            self.yawn_timer -= 1
            if self.yawn_timer <= 0:
                self.is_yawning = False
        elif idle_time > 60 and random.random() < 0.005 and not self.is_walking and not self.shake_angry:
            self.is_yawning = True
            self.yawn_timer = 40

        if self.is_sitting:
            self.sit_timer -= 1
            if self.sit_timer <= 0:
                self.is_sitting = False
        elif (self.x <= 20 or self.x >= self.screen_w - 100) and not self.is_walking and not self.shake_angry:
            if random.random() < 0.002:
                self.is_sitting = True
                self.sit_timer = 200

        status = self.save_manager.get_status()
        anger_level = self.save_manager.get_anger_level()

        if self.shake_angry:
            self.walk_mode = 'hide'
            self.walk_speed = 0
        elif status == 'happy':
            self.walk_mode = 'hop'
            self.walk_speed = 3
        elif status in ['sad', 'hungry']:
            self.walk_mode = 'slow'
            self.walk_speed = 1
        elif status == 'angry':
            if anger_level >= 3:
                self.walk_mode = 'run'
                self.walk_speed = 6
            elif anger_level >= 2:
                self.walk_mode = 'run'
                self.walk_speed = 4
            else:
                self.walk_mode = 'normal'
                self.walk_speed = 3
        else:
            self.walk_mode = 'normal'
            self.walk_speed = 2

    def _update_walking(self) -> None:
        if self.walk_pause_timer > 0:
            self.walk_pause_timer -= 1
            if self.walk_pause_timer == 80:
                self.is_looking_around = True
                self.look_direction = 'left'
                self.look_count = 0
                self.look_timer = 25
            elif self.walk_pause_timer == 0:
                self.is_looking_around = False
            return

        if self.is_looking_around:
            self.look_timer -= 1
            if self.look_timer <= 0:
                self.look_count += 1
                if self.look_count >= 2:
                    self.is_looking_around = False
                else:
                    self.look_direction = 'right' if self.look_direction == 'left' else 'left'
                    self.look_timer = 25

        if random.random() < 0.005:
            self.walk_pause_timer = 100
            return

        speed = self.walk_speed
        if self.walk_mode == 'hop':
            speed = 3
            if self.walk_tick % 20 == 0 and not self.jumping:
                self.jumping = True
                self.jump_vy = -6
                self.jump_y = 0.0
        elif self.walk_mode == 'run':
            speed = 5

        self.x += speed * self.walk_direction

        body_type = self.save_manager.get_body_type()
        sprite_w = 12 * sprites.PIXEL_SIZE if body_type == 'fat' else 10 * sprites.PIXEL_SIZE

        if self.x <= 10:
            self.walk_direction = 1
        elif self.x >= self.screen_w - sprite_w - 30:
            self.walk_direction = -1

        self.walk_tick += 1
        frame_speed = 5 if self.walk_mode == 'run' else 10
        if self.walk_tick % frame_speed == 0:
            self.walk_frame = 1 - self.walk_frame

        self.root.geometry(f'+{self.x}+{self.y}')
        self.bubble.update_position()
        self.paper_bubble.update_position()

    def _decay_loop(self) -> None:
        now = time.time()
        elapsed = now - self.last_decay_time

        self.save_manager.check_daily_settlement()
        self.save_manager.record_pre_sleep_mood()

        if elapsed >= self.decay_interval:
            hours = elapsed / 3600
            self.save_manager.apply_mood_decay(2.0, hours)
            self.save_manager.apply_decay(elapsed)
            self.save_manager.update_body_type()
            self.body_type = self.save_manager.get_body_type()
            self.last_decay_time = now

            from datetime import datetime
            if datetime.now().hour == 8:
                self.save_manager.clear_bad_sleep()

            status = self.save_manager.get_status()
            if status in ['hungry', 'dirty', 'sad', 'sick']:
                self.bubble.say_random(status)

        self._check_dream_trigger()
        self._check_paper_reminder()
        self.root.after(10000, self._decay_loop)

    def _auto_save(self) -> None:
        """自动保存"""
        self.save_manager.save()
        self.root.after(self.save_interval, self._auto_save)

    def _on_press(self, event: tk.Event) -> None:
        """鼠标按下"""
        if event.state & 0x4:  # Control 键
            return
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
        self._press_rx = event.x_root
        self._press_ry = event.y_root
        self.drag_data['dragging'] = False

    def _on_drag(self, event: tk.Event) -> None:
        """拖拽"""
        if event.state & 0x4:
            return

        dx = event.x_root - self._press_rx
        dy = event.y_root - self._press_ry
        if abs(dx) > 3 or abs(dy) > 3:
            self.drag_data['dragging'] = True

        if self.drag_data['dragging']:
            new_x = self.root.winfo_x() + (event.x - self.drag_data['x'])
            new_y = self.root.winfo_y() + (event.y - self.drag_data['y'])

            # 记录拖拽历史用于检测晃动
            now = time.time()
            self.drag_history.append((now, new_x, new_y))
            # 只保留最近0.5秒的记录
            self.drag_history = [(t, x, y) for t, x, y in self.drag_history
                                  if now - t < 0.5]

            # 检测晃动程度
            if len(self.drag_history) >= 5:
                self._check_shake()

            self.x = new_x
            self.y = new_y
            self.root.geometry(f'+{new_x}+{new_y}')
            self.bubble.update_position()
            self.paper_bubble.update_position()

            # 拖拽时停止走动
            if self.is_walking:
                self.is_walking = False

    def _check_shake(self) -> None:
        """检测是否在剧烈晃动"""
        if self.is_dizzy or self.is_falling:
            return

        if len(self.drag_history) < 6:
            return

        # 计算移动距离总和和方向变化次数
        total_distance = 0
        direction_changes = 0
        prev_dx, prev_dy = 0, 0

        for i in range(1, len(self.drag_history)):
            _, x1, y1 = self.drag_history[i - 1]
            _, x2, y2 = self.drag_history[i]
            dx = x2 - x1
            dy = y2 - y1
            total_distance += abs(dx) + abs(dy)

            # 检测方向变化（x或y方向反转）
            if (prev_dx * dx < 0) or (prev_dy * dy < 0):
                direction_changes += 1

            prev_dx, prev_dy = dx, dy

        # 必须同时满足：移动距离够大 + 方向变化够多（真正的晃动）
        if total_distance > self.shake_threshold and direction_changes >= 4:
            self._start_dizzy()

    def _on_release(self, event: tk.Event) -> None:
        """鼠标释放"""
        if not self.drag_data['dragging']:
            self._handle_click()
        self.drag_data['dragging'] = False
        self.drag_history = []  # 清空拖拽历史
        self.base_y = self.y  # 更新基准位置

    def _handle_click(self) -> None:
        self.save_manager.record_click()
        self.save_manager.record_interaction()

        if self.save_manager.data.get('is_dead'):
            self.bubble.show('……(右键可以复活我)')
            return

        status = self.save_manager.get_status()

        if status == 'angry':
            anger_level = self.save_manager.get_anger_level()
            if anger_level >= 3:
                self.bubble.say_random('angry_severe')
            elif anger_level >= 2:
                self.bubble.say_random('angry')
            else:
                self.bubble.say_random('angry_mild')
            return

        if status == 'sleep':
            self._trigger_sleep_disturb()
            return

        if self.save_manager.check_morning_greeting():
            self.bubble.show('早安！新的一天开始啦~')
            self.happy_timer = 40
            if not self.jumping:
                self.jumping = True
                self.jump_vy = self.jump_velocity
                self.jump_y = 0.0
            return

        self.happy_timer = 25
        if not self.jumping:
            self.jumping = True
            self.jump_vy = self.jump_velocity
            self.jump_y = 0.0

        self.bubble.say_random(status)

    def _feed(self) -> None:
        if self.save_manager.data.get('is_dead'):
            self.bubble.show('我已经……')
            return
        if self.is_eating:
            return

        if self.save_manager.is_sleep_time():
            self._trigger_sleep_disturb()
            return

        full_bonus, full_service = self.save_manager.feed()
        self.is_eating = True
        self.eat_timer = self.eat_duration
        self.eat_phase = 0
        sounds.play('feed')

        if full_service:
            self.bubble.show('全套服务！小铁皮超满足~')
        elif full_bonus:
            self.bubble.show('吃饱了！好满足~')
        else:
            self.bubble.show('好吃！谢谢~')

    def _bath(self) -> None:
        if self.save_manager.data.get('is_dead'):
            self.bubble.show('我已经……')
            return
        if self.is_bathing:
            return

        if self.save_manager.is_sleep_time():
            self._trigger_sleep_disturb()
            return

        clean_bonus, full_service = self.save_manager.bath()
        self.is_bathing = True
        self.bath_timer = self.bath_duration
        self.water_drops = []
        sounds.play('bath')

        if full_service:
            self.bubble.show('全套服务！小铁皮超满足~')
        elif clean_bonus:
            self.bubble.show('洗香香了！神清气爽~')
        else:
            self.bubble.show('洗干净啦！清爽~')

    def _play(self) -> None:
        if self.save_manager.data.get('is_dead'):
            self.bubble.show('我已经……')
            return
        if self.is_playing_game:
            return

        if self.save_manager.is_sleep_time():
            self._trigger_sleep_disturb()
            return

        full_service = self.save_manager.play()
        self.is_playing_game = True
        self.play_timer = self.play_duration
        self.button_blink_timer = 0
        sounds.play('play')

        if full_service:
            self.bubble.show('全套服务！小铁皮超满足~')
        else:
            self.bubble.show('好开心！(≧▽≦)')

    def _show_status(self) -> None:
        """显示状态"""
        status_text = self.save_manager.get_stats_display()
        messagebox.showinfo('小铁皮的状态', status_text)

    def _say_something(self) -> None:
        """随机说话"""
        status = self.save_manager.get_status()
        self.bubble.say_random(status)

    def _toggle_walk(self) -> None:
        """切换走动状态"""
        if self.save_manager.data.get('is_dead'):
            return

        self.is_walking = not self.is_walking
        if self.is_walking:
            self.walk_direction = random.choice([-1, 1])
            self.walk_tick = 0
            self.walk_frame = 0
            self.bubble.show('出发啦~')
        else:
            self.bubble.show('休息一下~')

    def _teach_dialogue(self) -> None:
        """教小铁皮说话"""
        # 创建输入对话框
        dialog = tk.Toplevel(self.root)
        dialog.title('教小铁皮说话')
        dialog.geometry('300x120')
        dialog.resizable(False, False)
        dialog.wm_attributes('-topmost', True)

        # 居中显示
        dialog.update_idletasks()
        x = (self.screen_w - 300) // 2
        y = (self.screen_h - 120) // 2
        dialog.geometry(f'+{x}+{y}')

        tk.Label(dialog, text='教它一句新的话：', font=('PingFang SC', 12)).pack(pady=10)

        entry = tk.Entry(dialog, width=30, font=('PingFang SC', 12))
        entry.pack(pady=5)
        entry.focus_set()

        def save_and_close():
            text = entry.get().strip()
            if text:
                if save_custom_dialogue(text):
                    self.bubble.show(f'学会了！"{text}"')
                else:
                    self.bubble.show('学不会…')
            dialog.destroy()

        def on_enter(event):
            save_and_close()

        entry.bind('<Return>', on_enter)

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text='教它！', command=save_and_close).pack(side='left', padx=5)
        tk.Button(btn_frame, text='取消', command=dialog.destroy).pack(side='left', padx=5)

    def _set_api_key(self) -> None:
        from paper_agent.api_key_manager import get_api_key, save_api_key, has_api_key

        dialog = tk.Toplevel(self.root)
        dialog.title('设置 API Key')
        dialog.geometry('400x150')
        dialog.resizable(False, False)
        dialog.wm_attributes('-topmost', True)

        dialog.update_idletasks()
        x = (self.screen_w - 400) // 2
        y = (self.screen_h - 150) // 2
        dialog.geometry(f'+{x}+{y}')

        tk.Label(dialog, text='Anthropic API Key:', font=('PingFang SC', 12)).pack(pady=10)

        entry = tk.Entry(dialog, width=45, font=('Monaco', 11), show='*')
        entry.pack(pady=5)

        current_key = get_api_key()
        if current_key:
            entry.insert(0, current_key)

        status_label = tk.Label(dialog, text='', font=('PingFang SC', 10))
        status_label.pack(pady=5)

        if has_api_key():
            status_label.config(text='✅ 已配置', fg='green')
        else:
            status_label.config(text='❌ 未配置', fg='red')

        def save_and_close():
            key = entry.get().strip()
            if key:
                if save_api_key(key):
                    self.bubble.show('API Key 保存成功！')
                else:
                    self.bubble.show('保存失败...')
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text='保存', command=save_and_close).pack(side='left', padx=5)
        tk.Button(btn_frame, text='取消', command=dialog.destroy).pack(side='left', padx=5)

    def _set_size(self, name: str, size: int) -> None:
        """设置大小"""
        self.current_size_name = name
        sprites.PIXEL_SIZE = size

        # 更新画布大小
        canvas_w, canvas_h = get_canvas_size()
        self.canvas.config(width=canvas_w, height=canvas_h)
        self.root.update_idletasks()

        self.bubble.show(f'变成{name}啦！')

    def _start_dizzy(self) -> None:
        self.is_dizzy = True
        self.dizzy_timer = 60
        self.drag_history = []
        self.shake_count += 1

        self.save_manager.modify_stat('happiness', -10)

        if self.shake_count >= 4:
            self.shake_angry = True
            self.shake_angry_timer = 300
            self.save_manager.modify_stat('happiness', -20)
            self.bubble.say_random('angry_shake')
        else:
            self.bubble.say_random('dizzy')

    def _start_falling(self) -> None:
        """开始下落"""
        self.is_falling = True
        self.fall_velocity = 0

    def _update_dizzy(self) -> None:
        """更新晕倒状态"""
        if not self.is_dizzy:
            return

        self.dizzy_timer -= 1

        if self.dizzy_timer <= 0:
            # 晕倒结束，开始下落
            self.is_dizzy = False
            self._start_falling()

    def _update_falling(self) -> None:
        """更新下落状态"""
        if not self.is_falling:
            return

        # 重力加速
        self.fall_velocity += 2
        self.y += self.fall_velocity

        # 计算屏幕底部位置
        sprite_h = 9 * sprites.PIXEL_SIZE
        ground_y = self.screen_h - sprite_h - 50

        if self.y >= ground_y:
            # 落地
            self.y = ground_y
            self.is_falling = False
            self.base_y = self.y
            self.bubble.say_random('recover')

        self.root.geometry(f'+{self.x}+{self.y}')
        self.bubble.update_position()

    def _update_bath(self) -> None:
        """更新洗澡动画"""
        if not self.is_bathing:
            return

        self.bath_timer -= 1

        # 喷头微微上下晃动
        self.shower_offset_y = int(math.sin(self.bath_timer * 0.2) * 2)

        # 生成新水滴（从喷头位置）
        if self.bath_timer % 3 == 0:
            ps = sprites.PIXEL_SIZE
            pad = ps * 2
            for _ in range(2):
                drop_x = pad + random.randint(2, 7) * ps
                drop_y = pad - 3 * ps + self.shower_offset_y
                self.water_drops.append({
                    'x': drop_x + random.randint(-2, 2),
                    'y': drop_y,
                    'speed': random.uniform(2, 4),
                    'size': random.choice([1, 2])
                })

        # 更新水滴位置
        for drop in self.water_drops:
            drop['y'] += drop['speed']
            drop['x'] += random.uniform(-0.5, 0.5)

        # 移除超出范围的水滴
        canvas_h = get_canvas_size()[1]
        self.water_drops = [d for d in self.water_drops if d['y'] < canvas_h + 10]

        # 动画结束
        if self.bath_timer <= 0:
            self.is_bathing = False
            self.water_drops = []

    def _update_eating(self) -> None:
        """更新喂食动画"""
        if not self.is_eating:
            return

        self.eat_timer -= 1

        # 咀嚼相位（快速循环）
        self.eat_phase = (self.eat_phase + 0.3) % (2 * math.pi)

        # 饭团逐渐被吃掉
        progress = 1 - (self.eat_timer / self.eat_duration)
        self.onigiri_offset = int(progress * 3)

        # 动画结束
        if self.eat_timer <= 0:
            self.is_eating = False
            self.onigiri_offset = 0

    def _update_playing(self) -> None:
        """更新玩耍动画"""
        if not self.is_playing_game:
            return

        self.play_timer -= 1

        # 手柄晃动
        self.controller_shake = math.sin(self.play_timer * 0.5) * 2

        # 按钮闪烁
        self.button_blink_timer = (self.button_blink_timer + 1) % 10

        # 动画结束
        if self.play_timer <= 0:
            self.is_playing_game = False
            self.controller_shake = 0

    def _draw_bath(self, pad: int, oy: int) -> None:
        """绘制洗澡动画"""
        if not self.is_bathing:
            return

        ps = sprites.PIXEL_SIZE
        colors = get_all_colors(self.save_manager.get_vitality())

        # 绘制喷头（在头顶上方）
        shower_head = SPRITE_SHOWER_HEAD
        shower_x = pad + 2 * ps
        shower_y = pad - 4 * ps + oy + self.shower_offset_y

        for r, row in enumerate(shower_head):
            for c, val in enumerate(row):
                if val == 0:
                    continue
                color = colors.get(val, '#A0A0A0')
                x1 = shower_x + c * ps
                y1 = shower_y + r * ps
                self.canvas.create_rectangle(
                    x1, y1, x1 + ps, y1 + ps,
                    fill=color, outline=color
                )

        # 绘制水滴
        for drop in self.water_drops:
            size = drop['size'] * 2
            self.canvas.create_rectangle(
                drop['x'], drop['y'],
                drop['x'] + size, drop['y'] + size * 1.5,
                fill='#87CEEB', outline='#87CEEB'
            )

    def _draw_eating(self, pad: int, oy: int) -> None:
        """绘制喂食动画"""
        if not self.is_eating:
            return

        ps = sprites.PIXEL_SIZE
        colors = get_all_colors(self.save_manager.get_vitality())

        # 咀嚼动作偏移
        chew_offset = int(math.sin(self.eat_phase) * 1.5)

        # 计算饭团位置（在嘴边）
        flip = self.walk_direction == -1
        if flip:
            onigiri_x = pad - 2 * ps - self.onigiri_offset
        else:
            onigiri_x = pad + 9 * ps + self.onigiri_offset
        onigiri_y = pad + 4 * ps + oy + chew_offset

        # 绘制饭团（随着时间减少显示的部分）
        progress = 1 - (self.eat_timer / self.eat_duration)
        visible_cols = max(1, int(5 * (1 - progress)))

        onigiri = SPRITE_ONIGIRI
        if flip:
            onigiri = [row[::-1] for row in onigiri]
            start_col = 5 - visible_cols
        else:
            start_col = 0

        for r, row in enumerate(onigiri):
            for c in range(start_col, min(start_col + visible_cols, len(row))):
                val = row[c]
                if val == 0:
                    continue
                color = colors.get(val, '#FFFFFF')
                x1 = onigiri_x + (c - start_col) * ps
                y1 = onigiri_y + r * ps
                self.canvas.create_rectangle(
                    x1, y1, x1 + ps, y1 + ps,
                    fill=color, outline=color
                )

    def _draw_playing(self, pad: int, oy: int) -> None:
        """绘制玩耍动画"""
        if not self.is_playing_game:
            return

        ps = sprites.PIXEL_SIZE
        colors = get_all_colors(self.save_manager.get_vitality())

        # 手柄位置（在身体前方）
        flip = self.walk_direction == -1
        controller_x = pad + 2 * ps
        controller_y = pad + 5 * ps + oy + int(self.controller_shake)

        controller = SPRITE_PS4_CONTROLLER
        if flip:
            controller = [row[::-1] for row in controller]

        # 绘制手柄
        for r, row in enumerate(controller):
            for c, val in enumerate(row):
                if val == 0:
                    continue
                # 按钮区域闪烁效果
                if val == 21 and self.button_blink_timer < 5:
                    color = '#4169E1'
                else:
                    color = colors.get(val, '#2D2D2D')
                x1 = controller_x + c * ps
                y1 = controller_y + r * ps
                self.canvas.create_rectangle(
                    x1, y1, x1 + ps, y1 + ps,
                    fill=color, outline=color
                )

        # 绘制手柄灯条
        if self.button_blink_timer < 5:
            light_x = controller_x + 3 * ps
            light_y = controller_y - ps // 2
            self.canvas.create_rectangle(
                light_x, light_y,
                light_x + ps, light_y + ps // 2,
                fill='#4169E1', outline='#4169E1'
            )

    # ========== 睡眠打扰系统 ==========

    def _trigger_sleep_disturb(self) -> None:
        count = self.save_manager.record_sleep_disturb()
        self.save_manager.modify_stat('happiness', -10 if self.shake_count > 0 else 0)

        if count == 1:
            self.sleep_disturb_state = 'sleepy'
            self.sleep_disturb_timer = 100
            msgs = ["嗯...？干嘛呀...", "现在几点了... 💤", "好困...不要吵人家...", "唔...让我再睡会..."]
        elif count == 2:
            self.sleep_disturb_state = 'annoyed'
            self.sleep_disturb_timer = 100
            msgs = ["又来！都说了在睡觉！😤", "你自己不睡觉吗！", "小铁皮要罢工了... 😑"]
        else:
            self.sleep_disturb_state = 'super_annoyed'
            self.sleep_disturb_timer = 100
            msgs = ["我不想理你了！！😡", "明天起来你给我等着！", "再吵我就离家出走！"]

        self.bubble.show(random.choice(msgs))

    def _update_sleep_disturb(self) -> None:
        if self.sleep_disturb_state and self.sleep_disturb_timer > 0:
            self.sleep_disturb_timer -= 1
            if self.sleep_disturb_timer <= 0:
                self.sleep_disturb_state = None

    # ========== 梦境系统 ==========

    def _check_dream_trigger(self) -> None:
        if not self.save_manager.is_sleep_time():
            return
        if self.is_dreaming or self.sleep_disturb_state:
            return

        now = time.time()
        if now - self.last_dream_time < 3600:
            return

        if random.random() < 0.02:
            self._start_dream()

    def _start_dream(self) -> None:
        pre_mood = self.save_manager.get_pre_sleep_mood()
        trust = self.save_manager.get_trust()

        if pre_mood >= 70:
            probs = {'good': 0.45, 'bad': 0.10, 'none': 0.45}
        elif pre_mood <= 30:
            probs = {'good': 0.15, 'bad': 0.40, 'none': 0.45}
        else:
            probs = {'good': 0.30, 'bad': 0.20, 'none': 0.50}

        r = random.random()
        if r < probs['good']:
            self.dream_type = 'good'
            self.save_manager.modify_stat('happiness', 5)
        elif r < probs['good'] + probs['bad']:
            self.dream_type = 'bad'
            self.save_manager.modify_stat('happiness', -5)
        else:
            self.dream_type = None
            return

        self.is_dreaming = True
        self.dream_timer = 200 if self.dream_type == 'good' else 160
        self.dream_icon_index = random.randint(0, 2)
        self.dream_float_phase = 0.0
        self.last_dream_time = time.time()

    def _update_dream(self) -> None:
        if not self.is_dreaming:
            return

        self.dream_timer -= 1
        self.dream_float_phase += 0.1

        if self.dream_timer <= 0:
            self._end_dream()

    def _end_dream(self) -> None:
        if self.dream_type == 'good':
            msgs = ["嘿嘿...梦到好吃的了...", "zzZ...好多星星...", "梦到被主人夸了...嘿嘿",
                    "梦里在跳舞...转圈圈...", "梦到了一个大大的拥抱..."]
        elif self.dream_type == 'bad':
            trust = self.save_manager.get_trust()
            msgs = ["呜...做了个噩梦...", "好可怕...梦到被格式化了", "噩梦...所有数据都丢了...",
                    "吓死小铁皮了...还好是梦"]
            if trust < 80:
                msgs.append("梦到主人不要我了...")
        else:
            msgs = []

        if msgs:
            self.bubble.show(random.choice(msgs))

        self.is_dreaming = False
        self.dream_type = None

    def _draw_dream(self, pad: int, oy: int) -> None:
        if not self.is_dreaming or not self.dream_type:
            return

        ps = sprites.PIXEL_SIZE
        colors = get_all_colors(self.save_manager.get_vitality())

        cloud = SPRITE_DREAM_CLOUD if self.dream_type == 'good' else SPRITE_NIGHTMARE_CLOUD
        icons = DREAM_ICONS_GOOD if self.dream_type == 'good' else DREAM_ICONS_BAD
        icon = icons[self.dream_icon_index % len(icons)]

        if self.dream_type == 'good':
            float_y = int(math.sin(self.dream_float_phase) * 3)
            float_x = 0
        else:
            float_y = 0
            float_x = int(math.sin(self.dream_float_phase * 2) * 2)

        cloud_x = pad + 6 * ps + float_x
        cloud_y = pad - 5 * ps + oy + float_y

        for r, row in enumerate(cloud):
            for c, val in enumerate(row):
                if val == 0:
                    continue
                color = colors.get(val, '#FFFFFF')
                x1 = cloud_x + c * ps // 2
                y1 = cloud_y + r * ps // 2
                self.canvas.create_rectangle(x1, y1, x1 + ps // 2, y1 + ps // 2, fill=color, outline=color)

        icon_x = cloud_x + 2 * ps
        icon_y = cloud_y + ps
        for r, row in enumerate(icon):
            for c, val in enumerate(row):
                if val == 0:
                    continue
                color = colors.get(val, '#FFD700')
                x1 = icon_x + c * ps // 2
                y1 = icon_y + r * ps // 2
                self.canvas.create_rectangle(x1, y1, x1 + ps // 2, y1 + ps // 2, fill=color, outline=color)

    # ========== 安慰系统 ==========

    def _comfort(self) -> None:
        if self.save_manager.data.get('is_dead'):
            self.bubble.show('我已经……')
            return

        if not self.save_manager.can_comfort():
            remaining = self.save_manager.get_comfort_cooldown_remaining()
            mins = remaining // 60
            self.bubble.show(f'刚被安慰过啦...再等{mins}分钟')
            return

        if self.save_manager.comfort():
            self.is_being_comforted = True
            self.comfort_timer = 60
            msgs = ["谢谢你...小铁皮好多了 🥺", "你还记得我...呜呜",
                    "被安慰了，小铁皮充满力量！", "这个拥抱好温暖..."]
            self.bubble.show(random.choice(msgs))

    def _update_comfort(self) -> None:
        if self.is_being_comforted:
            self.comfort_timer -= 1
            if self.comfort_timer <= 0:
                self.is_being_comforted = False

    # ========== 随机开心事件 ==========

    def _check_random_happy_event(self) -> None:
        if self.happy_event_active:
            return
        if self.save_manager.data.get('is_dead'):
            return
        if self.save_manager.is_sleep_time():
            return

        now = time.time()
        if now - self.last_happy_event_check < 1800:
            return

        self.last_happy_event_check = now

        if random.random() < 0.15:
            self._start_happy_event()

    def _start_happy_event(self) -> None:
        event_type = random.choice(['butterfly', 'cookie', 'music'])
        self.happy_event_active = True
        self.happy_event_type = event_type
        self.happy_event_timer = 150
        self.happy_event_phase = 0.0

        ps = sprites.PIXEL_SIZE
        if event_type == 'butterfly':
            self.happy_event_pos = [self.x + 15 * ps, self.y - 2 * ps]
        elif event_type == 'cookie':
            self.happy_event_pos = [self.x + 10 * ps, self.y + 8 * ps]
        else:
            self.happy_event_pos = [self.x + 12 * ps, self.y - 3 * ps]

        bonus = random.randint(3, 5)
        self.save_manager.apply_mood_gain(bonus)

        msgs = {
            'butterfly': '哇！有蝴蝶飞过来了！',
            'cookie': '诶？地上有块饼干耶！',
            'music': '这首歌好好听～ ♪'
        }
        self.root.after(500, lambda: self.bubble.show(msgs[event_type]))

    def _update_happy_event(self) -> None:
        if not self.happy_event_active:
            return

        self.happy_event_timer -= 1
        self.happy_event_phase += 0.15

        if self.happy_event_type == 'butterfly':
            self.happy_event_pos[0] += math.sin(self.happy_event_phase) * 2
            self.happy_event_pos[1] += math.cos(self.happy_event_phase * 0.5) * 1.5
        elif self.happy_event_type == 'music':
            self.happy_event_pos[1] -= 0.5

        if self.happy_event_timer <= 0:
            self.happy_event_active = False
            self.happy_event_type = None

    def _draw_happy_event(self, pad: int, oy: int) -> None:
        if not self.happy_event_active or not self.happy_event_type:
            return

        ps = sprites.PIXEL_SIZE
        colors = get_all_colors(self.save_manager.get_vitality())
        colors.update(ANIMATION_COLORS)

        sprite = HAPPY_EVENT_SPRITES.get(self.happy_event_type)
        if not sprite:
            return

        alpha = min(1.0, self.happy_event_timer / 30.0)

        base_x = int(self.happy_event_pos[0] - self.x + pad)
        base_y = int(self.happy_event_pos[1] - self.y + pad + oy)

        for r, row in enumerate(sprite):
            for c, val in enumerate(row):
                if val == 0:
                    continue
                color = colors.get(val, '#FFFFFF')
                x1 = base_x + c * ps // 2
                y1 = base_y + r * ps // 2
                self.canvas.create_rectangle(x1, y1, x1 + ps // 2, y1 + ps // 2, fill=color, outline=color)

    # ========== 论文阅读系统 ==========

    def _schedule_paper_fetch(self) -> None:
        now = datetime.now()
        if now.hour >= 6:
            self._check_paper_fetch()
        self.root.after(3600000, self._schedule_paper_fetch)

    def _check_paper_fetch(self) -> None:
        if self.paper_fetching:
            return

        try:
            from paper_agent.fetcher import PaperFetcher
            fetcher = PaperFetcher()

            if fetcher.should_fetch_today():
                self._start_paper_fetch()
            else:
                self.today_papers = fetcher.load_today_papers()
                if self.today_papers and not self._briefing_delivered():
                    self.paper_briefing_ready = True
                    # 如果有论文但还没推送过，尝试弹气泡
                    self._try_paper_bubble()
        except Exception as e:
            print(f"Paper check error: {e}")

    def _try_paper_bubble(self) -> None:
        """尝试弹出论文气泡提醒"""
        # 如果窗口已打开，不弹气泡
        if self.paper_chat_window:
            return

        # 检查是否有高分论文
        high_score_papers = [p for p in self.today_papers if p.get('interest_score', 0) >= 4]

        if high_score_papers:
            self.paper_bubble.show_paper_bubble(
                'high_score_paper',
                on_click=self._open_paper_chat
            )
        elif self.today_papers:
            self.paper_bubble.show_paper_bubble(
                'new_papers',
                on_click=self._open_paper_chat,
                count=len(self.today_papers)
            )

    def _check_paper_reminder(self) -> None:
        """检查是否需要提醒看论文"""
        # 如果窗口已打开，不提醒
        if self.paper_chat_window:
            return

        # 超过24小时没看论文
        if self.paper_bubble.hours_since_last_open() > 24:
            if self.today_papers and self.paper_bubble.can_show_bubble():
                self.paper_bubble.show_paper_bubble(
                    'reminder',
                    on_click=self._open_paper_chat
                )

    def _briefing_delivered(self) -> bool:
        try:
            from paper_agent.config import PAPER_DATA_FILE
            import json
            if PAPER_DATA_FILE.exists():
                with open(PAPER_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('briefing_delivered', False)
        except:
            pass
        return False

    def _start_paper_fetch(self) -> None:
        self.paper_fetching = True
        self.is_reading_papers = True
        self.reading_timer = 0
        self.bubble.show('让我看看今天有什么新论文... 🤓')

        def fetch_task():
            try:
                from paper_agent.fetcher import PaperFetcher
                from paper_agent.summarizer import PaperSummarizer
                from paper_agent.taste import TasteProfile

                fetcher = PaperFetcher()
                papers = fetcher.fetch_all()

                if papers:
                    summarizer = PaperSummarizer()
                    papers = summarizer.summarize_papers(papers)
                    summarizer.save_summarized_papers(papers)

                    taste = TasteProfile()
                    taste.update_from_papers(papers)

                    self.today_papers = papers
                    self.root.after(0, self._on_paper_fetch_done)
                else:
                    self.root.after(0, self._on_paper_fetch_failed)

            except Exception as e:
                print(f"Paper fetch error: {e}")
                self.root.after(0, self._on_paper_fetch_failed)

        threading.Thread(target=fetch_task, daemon=True).start()

    def _on_paper_fetch_done(self) -> None:
        self.paper_fetching = False
        self.push_glasses_timer = 30
        self.paper_briefing_ready = True

        # 检查是否有高分论文
        high_score_papers = [p for p in self.today_papers if p.get('interest_score', 0) >= 4]
        count = len(self.today_papers)

        # 如果窗口没打开，用论文气泡推送
        if not self.paper_chat_window:
            if high_score_papers:
                self.paper_bubble.show_paper_bubble(
                    'high_score_paper',
                    on_click=self._open_paper_chat
                )
            else:
                self.paper_bubble.show_paper_bubble(
                    'new_papers',
                    on_click=self._open_paper_chat,
                    count=count
                )
        else:
            deep_read_count = sum(1 for p in self.today_papers if p.get('deep_read'))
            self.bubble.show(f'读完今天的论文了！\n有 {deep_read_count} 篇挺有意思的', duration=5000)

    def _on_paper_fetch_failed(self) -> None:
        self.paper_fetching = False
        self.is_reading_papers = False
        self.bubble.show('今天网络不太好，没读到论文 😔')

    def _open_paper_chat(self) -> None:
        if self.paper_chat_window:
            return

        if not self.today_papers:
            self._check_paper_fetch()
            if not self.today_papers:
                self.bubble.show('今天还没有论文呢...稍等一下？')
                return

        self.is_reading_papers = True

        # 隐藏论文气泡
        self.paper_bubble.hide()

        try:
            from paper_agent.chat_window import PaperChatWindow
            self.paper_chat_window = PaperChatWindow(
                self.root,
                self.today_papers,
                on_close=self._on_paper_chat_close
            )
            self.paper_chat_window.show()

            # 记录打开时间
            self.paper_bubble.record_open()
            self._mark_briefing_delivered()
        except Exception as e:
            print(f"Open chat error: {e}")
            self.bubble.show('打开论文界面失败了...')

    def _on_paper_chat_close(self) -> None:
        self.paper_chat_window = None
        self.is_reading_papers = False

    def _mark_briefing_delivered(self) -> None:
        try:
            from paper_agent.config import PAPER_DATA_FILE
            import json
            if PAPER_DATA_FILE.exists():
                with open(PAPER_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data['briefing_delivered'] = True
                with open(PAPER_DATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass
        self.paper_briefing_ready = False

    def _update_reading(self) -> None:
        if not self.is_reading_papers:
            return

        self.reading_timer += 1

        if self.reading_timer % 60 == 0:
            self.reading_eye_phase = (self.reading_eye_phase + 1) % 3

        if self.push_glasses_timer > 0:
            self.push_glasses_timer -= 1

    def _draw_paper(self, pad: int, oy: int) -> None:
        if not self.is_reading_papers:
            return

        ps = sprites.PIXEL_SIZE
        colors = get_all_colors(self.save_manager.get_vitality())

        paper_x = pad + 8 * ps
        paper_y = pad + 5 * ps + oy

        for r, row in enumerate(SPRITE_PAPER):
            for c, val in enumerate(row):
                if val == 0:
                    continue
                color = colors.get(val, '#FFFFFF')
                x1 = paper_x + c * ps
                y1 = paper_y + r * ps
                self.canvas.create_rectangle(x1, y1, x1 + ps, y1 + ps, fill=color, outline=color)

    def _revive(self) -> None:
        if not self.save_manager.data.get('is_dead'):
            return
        self.save_manager.revive()
        self.bubble.show('我又活过来啦！')

    def _quit(self) -> None:
        """退出"""
        self.save_manager.save()
        self.bubble.hide()
        self.paper_bubble.hide()
        self.root.destroy()

    def run(self) -> None:
        """启动主循环"""
        self.root.mainloop()
