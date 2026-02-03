"""
bubble.py - 小铁皮的对话气泡模块
"""

import tkinter as tk
from typing import Optional, Callable, List
from pathlib import Path
import random
import json
from datetime import datetime, date

# 自定义台词文件路径
CUSTOM_DIALOGUES_FILE = Path.home() / '.xiaotiepi' / 'my_dialogues.txt'
BUBBLE_STATE_FILE = Path.home() / '.xiaotiepi' / 'bubble_state.json'

# 论文推送气泡内容模板
PAPER_BUBBLE_MESSAGES = {
    'high_score_paper': [
        "今天有篇论文超棒！快来看！ 👀",
        "发现了一篇很厉害的论文！",
        "这篇你肯定感兴趣！✨",
    ],
    'new_papers': [
        "今天找到了 {count} 篇新论文~",
        "新鲜出炉！{count} 篇论文等你看",
        "学术日报更新啦~ 📰",
    ],
    'reminder': [
        "好久没看论文了，要不要看看？",
        "论文们在等你呢~",
        "今天的日报还没看哦",
    ],
    'bookmark_reminder': [
        "你收藏的论文还没看呢~",
        "收藏夹里有论文等着你~",
    ],
}

# 不同状态的台词库
DIALOGUES = {
    'idle': [
        '今天也要加油哦！',
        '在忙什么呢？',
        '(*´▽`*)',
        '摸摸~',
        '嘿嘿~',
        '写代码要记得休息眼睛~',
        '喝水了吗？',
        '我是小铁皮！',
    ],
    'happy': [
        '好开心！(≧▽≦)',
        '嘻嘻~谢谢你照顾我',
        '今天心情超好的！',
        '你对我真好~',
        '爱你哦！♥',
    ],
    'hungry': [
        '好饿啊…给我吃东西嘛',
        '肚子咕咕叫了…',
        '有吃的吗？(´；ω；`)',
        '饿得眼冒金星…',
        '食物…食物…',
    ],
    'dirty': [
        '我身上是不是有味道了…',
        '帮我洗澡嘛…',
        '好想泡澡啊…',
        '脏脏的不开心(´・ω・`)',
        '需要清洁一下了…',
    ],
    'sad': [
        '好无聊啊…陪我玩一下嘛',
        '(´;︵;`)',
        '有点寂寞…',
        '你是不是忘记我了…',
        '想要被关注…',
    ],
    'sick': [
        '我不太舒服…',
        '头好晕…',
        '好难受…(´；Д；`)',
        '救救我…',
        '快照顾我一下嘛…',
    ],
    'angry_mild': [
        '嗯？又点我？',
        '在摸鱼吗~',
        '专心一点啦',
        '别老点我嘛',
    ],
    'angry': [
        '又在摸鱼！！',
        '别玩了去学习！',
        '别戳我了！专心工作！',
        '哼！(`ε´)',
        '摸鱼被我抓到了吧！',
        '工作！学习！别玩了！',
    ],
    'angry_severe': [
        '我不想理你了！！',
        '哼！！！(╯°□°)╯',
        '烦死了！！走开！！',
        '我要躲起来！！',
        '太过分了！！！',
    ],
    'angry_shake': [
        '你干嘛一直晃我！！',
        '头好晕！！你故意的！！',
        '我生气了！！不理你了！',
        '够了！！！(╯°Д°)╯',
        '再晃我就咬你！！',
    ],
    # 冷战期间的对话
    'cold_war': [
        '...',
        '哼',
        '还在生气',
        '不想说话',
        '别碰我',
    ],
    'cold_war_feed': [
        '哼...吃还是要吃的',
        '...谢什么谢',
        '别以为这样就没事了',
    ],
    'cold_war_feed_super': [
        '...你以为喂我就没事了？',
        '哼，还不够',
        '...先跟我道歉',
    ],
    'cold_war_softened': [
        '...好吧，至少你还记得喂我',
        '...有点感动，但还是要道歉',
    ],
    'calm_down': [
        '好吧...原谅你了',
        '这次就算了...',
        '下次不许了！',
    ],
    'apology_accepted': [
        '...好吧，这次原谅你了 😤',
        '哼...算你有诚意',
        '下次不许再这样了！',
    ],
    'apology_wrong': [
        '哼，不是这样说的！',
        '...你觉得这样就行了？',
        '诚意呢？',
    ],
    # 深夜打扰
    'night_disturb_1': [
        '唔...困...别吵...',
        '让我睡嘛...',
        'zzZ...嗯？',
    ],
    'night_disturb_2': [
        '都说了在睡觉！',
        '又来！让我睡！',
        '你不睡觉吗！',
    ],
    'night_disturb_3': [
        '！！！不睡觉了是吧！！',
        '够了！！都不让我睡！！',
        '我生气了！！！',
    ],
    # 难过系统
    'sad': [
        '唉...',
        '有点难过',
        '你是不是忘了我...',
        '好无聊啊',
        '肚子饿...',
    ],
    'very_sad': [
        '...',
        '不想动',
        '你还在吗...',
        '是不是不要我了',
    ],
    # 复合情绪（又气又饿等）
    'angry_hungry': [
        '哼...而且肚子饿了...',
        '生气...还饿...',
        '哼，饿死了都不管我',
    ],
    'angry_dirty': [
        '哼...而且身上脏脏的...',
        '生气，还没洗澡...',
    ],
    'lonely': [
        '你是不是把我忘了…',
        '好久没人理我了…(´・ω・`)',
        '我一个人好孤单…',
        '已经好几个小时没人来看我了…',
        '喂…有人在吗…',
        '呜呜…寂寞…',
        '你去哪里了嘛…',
        '我还以为你不要我了…',
    ],
    'sleep': [
        'zzZ…zzZ…',
        '(睡着了…)',
        '呼…呼…',
        '梦到好吃的了…zzZ',
        '别吵…让我再睡会儿…',
    ],
    'dead': [
        '……',
        '(已离线)',
    ],
    'dizzy': [
        '头好晕…@@',
        '天旋地转…',
        '别晃我啦…',
        '世界在转…',
        '我…我要倒了…',
    ],
    'recover': [
        '呼…终于不晕了',
        '我没事了…',
        '下次轻点晃…',
        '站起来了！',
    ],
    'night': [
        '这么晚了还不睡吗？',
        '早点休息吧~',
        '熬夜对身体不好哦',
        '该睡觉啦 (￣o￣) zzZZ',
        '明天再继续吧~',
    ],
}


def load_custom_dialogues() -> List[str]:
    """加载用户自定义台词"""
    if not CUSTOM_DIALOGUES_FILE.exists():
        # 创建示例文件
        CUSTOM_DIALOGUES_FILE.parent.mkdir(parents=True, exist_ok=True)
        CUSTOM_DIALOGUES_FILE.write_text(
            "# 在这里添加自定义台词，每行一句\n"
            "# 以 # 开头的行是注释，会被忽略\n"
            "你好呀！\n"
            "今天也要元气满满！\n",
            encoding='utf-8'
        )

    try:
        lines = CUSTOM_DIALOGUES_FILE.read_text(encoding='utf-8').splitlines()
        # 过滤空行和注释
        return [line.strip() for line in lines
                if line.strip() and not line.strip().startswith('#')]
    except Exception:
        return []


def save_custom_dialogue(text: str) -> bool:
    """保存一条新的自定义台词"""
    try:
        CUSTOM_DIALOGUES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CUSTOM_DIALOGUES_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{text}\n")
        return True
    except Exception:
        return False


class Bubble:
    """对话气泡"""

    def __init__(self, parent_window: tk.Tk):
        self.parent = parent_window
        self.window: Optional[tk.Toplevel] = None
        self.hide_job: Optional[str] = None
        self.label: Optional[tk.Label] = None

    def show(self, text: str, duration: int = 3000) -> None:
        self.hide()

        self.window = tk.Toplevel(self.parent)
        self.window.overrideredirect(True)
        self.window.wm_attributes('-topmost', True)

        try:
            self.window.wm_attributes('-transparent', True)
            self.window.config(bg='systemTransparent')
            bg_color = 'systemTransparent'
        except tk.TclError:
            bg_color = '#2D2D2D'
            self.window.config(bg=bg_color)

        temp_label = tk.Label(self.window, text=text, font=('PingFang SC', 11))
        temp_label.update_idletasks()
        text_w = max(80, temp_label.winfo_reqwidth() + 20)
        text_h = temp_label.winfo_reqheight() + 16
        temp_label.destroy()

        ps = 3
        canvas_w = text_w + ps * 4
        canvas_h = text_h + ps * 4 + ps * 3

        canvas = tk.Canvas(self.window, width=canvas_w, height=canvas_h,
                          highlightthickness=0, bg=bg_color)
        canvas.pack()

        border_color = '#D4856A'
        fill_color = '#FFF5EE'

        for i in range(ps, canvas_w - ps, ps):
            canvas.create_rectangle(i, 0, i + ps, ps, fill=border_color, outline=border_color)
            canvas.create_rectangle(i, text_h + ps * 3, i + ps, text_h + ps * 4,
                                   fill=border_color, outline=border_color)

        for i in range(ps, text_h + ps * 3, ps):
            canvas.create_rectangle(0, i, ps, i + ps, fill=border_color, outline=border_color)
            canvas.create_rectangle(canvas_w - ps, i, canvas_w, i + ps,
                                   fill=border_color, outline=border_color)

        canvas.create_rectangle(ps, ps, canvas_w - ps, text_h + ps * 3,
                               fill=fill_color, outline=fill_color)

        tail_x = canvas_w // 2
        tail_y = text_h + ps * 4
        for i, w in enumerate([3, 2, 1]):
            canvas.create_rectangle(tail_x - w * ps, tail_y + i * ps,
                                   tail_x + w * ps, tail_y + (i + 1) * ps,
                                   fill=border_color, outline=border_color)

        self.label = tk.Label(canvas, text=text, font=('PingFang SC', 11),
                             bg=fill_color, fg='#333333', wraplength=150, justify='left')
        canvas.create_window(canvas_w // 2, (text_h + ps * 4) // 2, window=self.label)

        self._update_position()
        self.hide_job = self.parent.after(duration, self.hide)

    def _update_position(self) -> None:
        """更新气泡位置（在宠物上方）"""
        if not self.window:
            return

        try:
            # 获取父窗口位置
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()

            # 气泡在宠物上方
            bubble_x = parent_x
            bubble_y = parent_y - 60

            self.window.geometry(f'+{bubble_x}+{bubble_y}')
        except tk.TclError:
            pass

    def hide(self) -> None:
        """隐藏气泡"""
        if self.hide_job:
            try:
                self.parent.after_cancel(self.hide_job)
            except (tk.TclError, ValueError):
                pass
            self.hide_job = None

        if self.window:
            try:
                self.window.destroy()
            except tk.TclError:
                pass
            self.window = None

    def update_position(self) -> None:
        """外部调用更新位置"""
        self._update_position()

    def say_random(self, status: str) -> None:
        """根据状态说随机台词"""
        hour = datetime.now().hour

        # 睡觉状态直接用睡觉台词
        if status == 'sleep':
            dialogues = DIALOGUES.get('sleep', [])
        # 深夜但不是睡觉状态时（比如被点击）
        elif hour >= 22 or hour < 6:
            dialogues = DIALOGUES.get('night', [])
        else:
            dialogues = DIALOGUES.get(status, DIALOGUES['idle'])

        # 正常/开心状态时，有机会说用户自定义的台词
        if status in ['idle', 'happy'] and random.random() < 0.3:
            custom = load_custom_dialogues()
            if custom:
                dialogues = custom

        if dialogues:
            text = random.choice(dialogues)
            self.show(text)


class PaperBubbleManager:
    """论文推送气泡管理器"""

    MAX_BUBBLES_PER_DAY = 3

    def __init__(self, parent_window: tk.Tk):
        self.parent = parent_window
        self.bubble_window: Optional[tk.Toplevel] = None
        self.hide_job: Optional[str] = None
        self.hover_paused = False
        self.on_click_callback: Optional[Callable] = None
        self._load_state()

    def _load_state(self) -> None:
        """加载气泡状态"""
        self.state = {
            'today': str(date.today()),
            'bubble_count': 0,
            'shown_messages': [],
            'last_open_time': None
        }

        if BUBBLE_STATE_FILE.exists():
            try:
                with open(BUBBLE_STATE_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                # 检查是否是今天
                if saved.get('today') == str(date.today()):
                    self.state = saved
                else:
                    self._save_state()
            except:
                pass

    def _save_state(self) -> None:
        """保存气泡状态"""
        try:
            BUBBLE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(BUBBLE_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False)
        except:
            pass

    def can_show_bubble(self) -> bool:
        """检查今天是否还能弹气泡"""
        # 确保是今天的状态
        if self.state.get('today') != str(date.today()):
            self.state = {
                'today': str(date.today()),
                'bubble_count': 0,
                'shown_messages': [],
                'last_open_time': None
            }
        return self.state['bubble_count'] < self.MAX_BUBBLES_PER_DAY

    def record_open(self) -> None:
        """记录用户打开日报的时间"""
        self.state['last_open_time'] = datetime.now().isoformat()
        self._save_state()

    def hours_since_last_open(self) -> float:
        """获取距离上次打开的小时数"""
        last_time = self.state.get('last_open_time')
        if not last_time:
            return 999
        try:
            last = datetime.fromisoformat(last_time)
            return (datetime.now() - last).total_seconds() / 3600
        except:
            return 999

    def show_paper_bubble(self, message_type: str, on_click: Callable = None,
                          count: int = 0) -> bool:
        """显示论文气泡

        Args:
            message_type: 消息类型 (high_score_paper, new_papers, reminder, bookmark_reminder)
            on_click: 点击回调
            count: 论文数量（用于 new_papers 类型）

        Returns:
            是否成功显示
        """
        if not self.can_show_bubble():
            return False

        messages = PAPER_BUBBLE_MESSAGES.get(message_type, [])
        if not messages:
            return False

        # 过滤已经显示过的消息
        available = [m for m in messages if m not in self.state['shown_messages']]
        if not available:
            # 如果全部都显示过了，重置
            available = messages

        message = random.choice(available)
        if '{count}' in message:
            message = message.format(count=count)

        self.on_click_callback = on_click
        self._show_bubble(message)

        # 记录
        self.state['bubble_count'] += 1
        self.state['shown_messages'].append(message)
        self._save_state()

        return True

    def _show_bubble(self, text: str, duration: int = 10000) -> None:
        """显示气泡"""
        self.hide()

        self.bubble_window = tk.Toplevel(self.parent)
        self.bubble_window.overrideredirect(True)
        self.bubble_window.wm_attributes('-topmost', True)

        try:
            self.bubble_window.wm_attributes('-transparent', True)
            self.bubble_window.config(bg='systemTransparent')
            bg_color = 'systemTransparent'
        except tk.TclError:
            bg_color = '#2D2D2D'
            self.bubble_window.config(bg=bg_color)

        # 计算文字尺寸
        temp_label = tk.Label(self.bubble_window, text=text, font=('PingFang SC', 11))
        temp_label.update_idletasks()
        text_w = max(100, min(180, temp_label.winfo_reqwidth() + 24))
        text_h = temp_label.winfo_reqheight() + 20
        temp_label.destroy()

        ps = 3
        canvas_w = text_w + ps * 4
        canvas_h = text_h + ps * 4 + ps * 3

        canvas = tk.Canvas(self.bubble_window, width=canvas_w, height=canvas_h,
                          highlightthickness=0, bg=bg_color)
        canvas.pack()

        # 暖色系配色（和聊天窗口一致）
        border_color = '#CD853F'
        fill_color = '#FFF5E6'

        # 绘制边框
        for i in range(ps, canvas_w - ps, ps):
            canvas.create_rectangle(i, 0, i + ps, ps, fill=border_color, outline=border_color)
            canvas.create_rectangle(i, text_h + ps * 3, i + ps, text_h + ps * 4,
                                   fill=border_color, outline=border_color)

        for i in range(ps, text_h + ps * 3, ps):
            canvas.create_rectangle(0, i, ps, i + ps, fill=border_color, outline=border_color)
            canvas.create_rectangle(canvas_w - ps, i, canvas_w, i + ps,
                                   fill=border_color, outline=border_color)

        # 填充背景
        canvas.create_rectangle(ps, ps, canvas_w - ps, text_h + ps * 3,
                               fill=fill_color, outline=fill_color)

        # 小三角（指向下方的小铁皮）
        tail_x = canvas_w // 2
        tail_y = text_h + ps * 4
        for i, w in enumerate([3, 2, 1]):
            canvas.create_rectangle(tail_x - w * ps, tail_y + i * ps,
                                   tail_x + w * ps, tail_y + (i + 1) * ps,
                                   fill=border_color, outline=border_color)

        # 文字标签
        label = tk.Label(canvas, text=text, font=('PingFang SC', 11),
                        bg=fill_color, fg='#3E2723', wraplength=160, justify='left',
                        cursor='hand2')
        canvas.create_window(canvas_w // 2, (text_h + ps * 4) // 2, window=label)

        # 绑定事件
        label.bind('<Button-1>', self._on_click)
        label.bind('<Enter>', self._on_enter)
        label.bind('<Leave>', self._on_leave)
        canvas.bind('<Button-1>', self._on_click)

        self._update_position()

        # 10秒后自动消失
        self.hide_job = self.parent.after(duration, self.hide)

    def _update_position(self) -> None:
        """更新气泡位置"""
        if not self.bubble_window:
            return

        try:
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()

            bubble_w = self.bubble_window.winfo_reqwidth()
            bubble_x = parent_x + 30 - bubble_w // 2
            bubble_y = parent_y - 70

            # 防止超出屏幕
            screen_w = self.parent.winfo_screenwidth()
            if bubble_x < 10:
                bubble_x = 10
            if bubble_x + bubble_w > screen_w - 10:
                bubble_x = screen_w - bubble_w - 10

            self.bubble_window.geometry(f'+{bubble_x}+{bubble_y}')
        except tk.TclError:
            pass

    def _on_click(self, event) -> None:
        """点击气泡"""
        if self.on_click_callback:
            self.on_click_callback()
        self.hide()

    def _on_enter(self, event) -> None:
        """鼠标进入，暂停消失计时"""
        self.hover_paused = True
        if self.hide_job:
            try:
                self.parent.after_cancel(self.hide_job)
            except:
                pass
            self.hide_job = None

    def _on_leave(self, event) -> None:
        """鼠标离开，恢复计时"""
        self.hover_paused = False
        if self.bubble_window and not self.hide_job:
            self.hide_job = self.parent.after(5000, self.hide)

    def hide(self) -> None:
        """隐藏气泡"""
        if self.hide_job:
            try:
                self.parent.after_cancel(self.hide_job)
            except:
                pass
            self.hide_job = None

        if self.bubble_window:
            try:
                self.bubble_window.destroy()
            except:
                pass
            self.bubble_window = None

        self.hover_paused = False

    def update_position(self) -> None:
        """更新位置（小铁皮移动时调用）"""
        self._update_position()
