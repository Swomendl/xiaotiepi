"""
casual_chat_window.py - 小铁皮·日常闲聊窗口
像素 RPG 风格，支持打字机效果
"""

import tkinter as tk
from tkinter import ttk
import threading
import json
import time
from datetime import datetime
from typing import List, Dict, Callable, Optional
from pathlib import Path

# 聊天历史文件
CASUAL_CHAT_DIR = Path.home() / '.xiaotiepi'
CASUAL_CHAT_HISTORY_FILE = CASUAL_CHAT_DIR / 'casual_chat_history.json'

# ===== 样式常量 =====
COLORS = {
    'bg': '#2D2B35',              # 深灰紫背景
    'border': '#FF9F43',          # 荧光橙边框
    'pet_text': '#FF9F43',        # 小铁皮文字（荧光橙）
    'user_text': '#55E6C1',       # 用户文字（像素绿）
    'input_bg': '#1E1E24',        # 输入框背景
    'input_text': '#DCDDE1',      # 输入框文字
    'title_bg': '#3D3A47',        # 标题栏背景
    'system_text': '#888888',     # 系统提示文字
    'cursor': '#FF9F43',          # 光标颜色
}

FONTS = {
    'title': ('Menlo', 11, 'bold'),
    'chat': ('Menlo', 11),
    'input': ('Menlo', 11),
    'small': ('Menlo', 9),
}

# 打字机速度
TYPEWRITER_CHAR_MS = 30    # 普通字符
TYPEWRITER_PUNCT_MS = 80   # 标点符号


class ChatHistory:
    """聊天历史管理"""

    def __init__(self):
        CASUAL_CHAT_DIR.mkdir(parents=True, exist_ok=True)
        self.messages = self._load()

    def _load(self) -> List[Dict]:
        """加载历史"""
        if CASUAL_CHAT_HISTORY_FILE.exists():
            try:
                with open(CASUAL_CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('messages', [])[-10:]  # 只保留最近 10 轮
            except:
                pass
        return []

    def save(self) -> None:
        """保存历史"""
        try:
            with open(CASUAL_CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'messages': self.messages[-10:],
                    'last_chat': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except:
            pass

    def add(self, role: str, content: str) -> None:
        """添加消息"""
        self.messages.append({
            'role': role,
            'content': content,
            'time': datetime.now().isoformat()
        })
        self.save()

    def get_context(self) -> List[Dict]:
        """获取对话上下文（用于 API 调用）"""
        return [{'role': m['role'], 'content': m['content']}
                for m in self.messages[-6:]]  # 最近 3 轮


class CasualChatWindow:
    """日常闲聊窗口"""

    def __init__(self, parent, save_manager, on_close: Callable = None):
        self.parent = parent
        self.save_manager = save_manager
        self.on_close = on_close
        self.history = ChatHistory()
        self.window = None
        self.is_typing = False
        self.typing_job = None

        # 拖拽状态
        self.drag_data = {'x': 0, 'y': 0}

    def show(self) -> None:
        """显示窗口"""
        if self.window:
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title('小铁皮·闲聊')
        self.window.attributes('-topmost', True)

        # 窗口大小（调大一点）
        self.width = 380
        self.height = 450

        # macOS 特殊窗口样式（保留输入功能）
        try:
            self.window.tk.call('::tk::unsupported::MacWindowStyle', 'style',
                               self.window._w, 'plain', 'none')
        except:
            pass

        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self._close)

        # 定位在小铁皮附近
        pet_x = self.parent.winfo_x()
        pet_y = self.parent.winfo_y()
        screen_w = self.parent.winfo_screenwidth()
        screen_h = self.parent.winfo_screenheight()

        # 优先放在右边
        x = pet_x + 120
        y = pet_y - 100

        # 确保不超出屏幕
        if x + self.width > screen_w:
            x = pet_x - self.width - 20
        if y < 0:
            y = 10
        if y + self.height > screen_h:
            y = screen_h - self.height - 50

        self.window.geometry(f'{self.width}x{self.height}+{x}+{y}')

        self._create_ui()
        self._show_opening()

        # macOS 焦点修复
        self.window.after(100, self._fix_focus)

    def _fix_focus(self) -> None:
        """修复 macOS 焦点问题"""
        try:
            self.window.focus_force()
            self.window.lift()
            self.input_entry.focus_set()
        except:
            pass

    def _create_ui(self) -> None:
        """创建 UI"""
        # 主框架（带边框）
        self.main_frame = tk.Frame(
            self.window,
            bg=COLORS['border'],
            padx=3,
            pady=3
        )
        self.main_frame.pack(fill='both', expand=True)

        # 内部框架
        inner = tk.Frame(self.main_frame, bg=COLORS['bg'])
        inner.pack(fill='both', expand=True)

        # 标题栏
        self._create_title_bar(inner)

        # 聊天区域
        self._create_chat_area(inner)

        # 输入区域
        self._create_input_area(inner)

    def _create_title_bar(self, parent) -> None:
        """创建标题栏"""
        title_bar = tk.Frame(parent, bg=COLORS['title_bg'], height=30)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)

        # 标题（可拖动）
        title_label = tk.Label(
            title_bar,
            text='[o_o] 小铁皮的内心世界',
            bg=COLORS['title_bg'],
            fg=COLORS['border'],
            font=FONTS['title']
        )
        title_label.pack(side='left', padx=10, pady=5)

        # 绑定拖动
        title_label.bind('<ButtonPress-1>', self._start_drag)
        title_label.bind('<B1-Motion>', self._do_drag)
        title_bar.bind('<ButtonPress-1>', self._start_drag)
        title_bar.bind('<B1-Motion>', self._do_drag)

        # 关闭按钮
        close_btn = tk.Label(
            title_bar,
            text='x',
            bg=COLORS['title_bg'],
            fg='#888888',
            font=FONTS['title'],
            cursor='hand2'
        )
        close_btn.pack(side='right', padx=10, pady=5)
        close_btn.bind('<Button-1>', lambda e: self._close())
        close_btn.bind('<Enter>', lambda e: close_btn.config(fg=COLORS['border']))
        close_btn.bind('<Leave>', lambda e: close_btn.config(fg='#888888'))

    def _create_chat_area(self, parent) -> None:
        """创建聊天区域"""
        chat_frame = tk.Frame(parent, bg=COLORS['bg'])
        chat_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 聊天文本框
        self.chat_text = tk.Text(
            chat_frame,
            bg=COLORS['bg'],
            fg=COLORS['pet_text'],
            font=FONTS['chat'],
            wrap='word',
            state='disabled',
            cursor='arrow',
            relief='flat',
            padx=5,
            pady=5
        )
        self.chat_text.pack(fill='both', expand=True)

        # 配置标签样式
        self.chat_text.tag_configure('pet', foreground=COLORS['pet_text'])
        self.chat_text.tag_configure('user', foreground=COLORS['user_text'])
        self.chat_text.tag_configure('system', foreground=COLORS['system_text'])
        self.chat_text.tag_configure('prefix', foreground=COLORS['user_text'])

    def _create_input_area(self, parent) -> None:
        """创建输入区域"""
        # 输入容器
        input_frame = tk.Frame(parent, bg=COLORS['input_bg'])
        input_frame.pack(fill='x', padx=10, pady=(5, 15))

        # 命令行风格前缀
        prefix_label = tk.Label(
            input_frame,
            text=' > ',
            bg=COLORS['input_bg'],
            fg=COLORS['user_text'],
            font=('Menlo', 13)
        )
        prefix_label.pack(side='left', pady=8)

        # 输入框
        self.input_entry = tk.Entry(
            input_frame,
            bg=COLORS['input_bg'],
            fg=COLORS['input_text'],
            font=('Menlo', 13),
            relief='flat',
            insertbackground=COLORS['cursor'],
            width=30
        )
        self.input_entry.pack(side='left', fill='x', expand=True, pady=8, padx=(0, 10))
        self.input_entry.bind('<Return>', self._on_send)
        self.input_entry.focus_set()

        # 发送按钮
        send_btn = tk.Label(
            input_frame,
            text='[送]',
            bg=COLORS['bg'],
            fg=COLORS['border'],
            font=FONTS['small'],
            cursor='hand2'
        )
        send_btn.pack(side='right')
        send_btn.bind('<Button-1>', self._on_send)

    def _start_drag(self, event) -> None:
        """开始拖动"""
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y

    def _do_drag(self, event) -> None:
        """执行拖动"""
        x = self.window.winfo_x() + event.x - self.drag_data['x']
        y = self.window.winfo_y() + event.y - self.drag_data['y']
        self.window.geometry(f'+{x}+{y}')

    def _show_opening(self) -> None:
        """显示开场白"""
        trust = self.save_manager.get_trust()
        happiness = self.save_manager.get_stat('happiness')

        # 根据状态选择开场白
        if happiness < 30:
            openings = [
                "...今天不太开心",
                "唔...有点累...",
                "能陪我说说话吗...",
            ]
        elif trust < 40:
            openings = [
                "嗯？你想聊天吗",
                "...有事吗？",
                "诶，是你啊",
            ]
        elif trust < 70:
            openings = [
                "来找我玩啦~",
                "嘿嘿，想聊点什么？",
                "正好有点无聊呢~",
            ]
        else:
            openings = [
                "是你！太好了~",
                "嘿嘿，来陪我啦",
                "今天想聊点什么呀~",
                "等你好久了！",
            ]

        import random
        opening = random.choice(openings)
        self._typewriter_effect(f"小铁皮: {opening}\n\n", 'pet')

    def _append_text(self, text: str, tag: str = None) -> None:
        """追加文本"""
        self.chat_text.config(state='normal')
        if tag:
            self.chat_text.insert('end', text, tag)
        else:
            self.chat_text.insert('end', text)
        self.chat_text.see('end')
        self.chat_text.config(state='disabled')

    def _typewriter_effect(self, text: str, tag: str = None) -> None:
        """打字机效果"""
        self.is_typing = True
        self.input_entry.config(state='disabled')

        def type_char(index=0):
            if index >= len(text):
                self.is_typing = False
                self.input_entry.config(state='normal')
                self.input_entry.focus_set()
                return

            char = text[index]
            self._append_text(char, tag)

            # 标点符号延迟更长
            if char in '，。！？、；：…~':
                delay = TYPEWRITER_PUNCT_MS
            else:
                delay = TYPEWRITER_CHAR_MS

            self.typing_job = self.window.after(delay, lambda: type_char(index + 1))

        type_char()

    def _on_send(self, event=None) -> None:
        """发送消息"""
        if self.is_typing:
            return

        text = self.input_entry.get().strip()
        if not text:
            return

        self.input_entry.delete(0, 'end')

        # 显示用户消息
        self._append_text(f"> {text}\n\n", 'user')

        # 保存到历史
        self.history.add('user', text)

        # 调用 API 获取回复
        self._get_reply(text)

    def _get_reply(self, user_message: str) -> None:
        """获取回复"""
        self.input_entry.config(state='disabled')

        def fetch():
            try:
                reply = self._call_api(user_message)
                self.window.after(0, lambda: self._show_reply(reply))
            except Exception as e:
                print(f"Chat API error: {e}")
                self.window.after(0, lambda: self._show_reply("唔...脑子有点卡"))

        threading.Thread(target=fetch, daemon=True).start()

    def _call_api(self, user_message: str) -> str:
        """调用 API"""
        # 调试日志
        from pathlib import Path
        log_file = Path.home() / '.xiaotiepi' / 'debug.log'
        def log(msg):
            try:
                with open(log_file, 'a') as f:
                    f.write(f"[chat] {msg}\n")
            except:
                pass

        log(f"_call_api called with: {user_message[:30]}...")

        try:
            from paper_agent.api_key_manager import get_api_key
            log("api_key_manager imported")

            import anthropic
            log(f"anthropic imported: {anthropic.__version__}")

            api_key = get_api_key()
            log(f"api_key found: {bool(api_key)}")

            if not api_key:
                return "我好像说不出话来...（没有 API Key）"

            client = anthropic.Anthropic(api_key=api_key)
            log("client created")

            # 构建 prompt
            system_prompt = self._build_pet_prompt()

            # 获取历史上下文
            messages = self.history.get_context()
            if not messages or messages[-1]['role'] != 'user':
                messages.append({'role': 'user', 'content': user_message})

            log("calling messages.create...")
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=150,
                system=system_prompt,
                messages=messages
            )
            log("response received")

            reply = response.content[0].text.strip()

            # 保存回复
            self.history.add('assistant', reply)
            log(f"reply: {reply[:30]}...")

            return reply

        except Exception as e:
            import traceback
            log(f"ERROR: {type(e).__name__}: {e}")
            log(traceback.format_exc())
            return "呜...说不出话来了"

    def _build_pet_prompt(self) -> str:
        """构建宠物人格 Prompt"""
        trust = self.save_manager.get_trust()
        happiness = self.save_manager.get_stat('happiness')
        hunger = self.save_manager.get_stat('hunger')

        # 根据亲密度等级调整性格
        if trust < 20:
            personality = "你有点害羞和警惕，话很少，不太信任用户，但内心想成为朋友。"
        elif trust < 40:
            personality = "你开始认识用户了，愿意多说几句，但还是有点保守。"
        elif trust < 60:
            personality = "你和用户是朋友了，会开玩笑，偶尔撒娇，比较放松。"
        elif trust < 80:
            personality = "你和用户是好朋友，会分享心事，会吐槽，会关心对方。"
        elif trust < 100:
            personality = "你和用户是最好的朋友，无话不谈，会耍赖，会任性，但也很体贴。"
        else:
            personality = "你和用户是灵魂伴侣级别的朋友，可以解锁一些特别的话题和彩蛋。"

        # 状态描述
        status_notes = []
        if hunger < 30:
            status_notes.append("你现在很饿，可以委婉提一下")
        if happiness < 30:
            status_notes.append("你现在心情不太好，可以表现出来")

        status_text = "；".join(status_notes) if status_notes else "状态还不错"

        return f'''你是小铁皮，一个像素风格的桌面电子宠物。

## 你和用户的关系
{personality}
亲密度：{int(trust)}/100

## 当前状态
心情 {int(happiness)}/100，饥饿 {int(hunger)}/100
{status_text}

## 说话风格
- 简短口语化，1-3句话
- 用 "嘛"、"呀"、"诶"、"唔" 等语气词
- 偶尔用颜文字但不要太多
- 不要太正式，不要用"您"
- 亲密度低时话少一点，高时话多一点、更亲昵

## 重要
这是日常闲聊，不是讨论论文！聊点轻松的。'''

    def _show_reply(self, reply: str) -> None:
        """显示回复"""
        self._typewriter_effect(f"小铁皮: {reply}\n\n", 'pet')

        # 增加亲密度和心情
        self.save_manager.add_trust(0.5, 'chat')
        self.save_manager.modify_stat('happiness', 2)
        self.save_manager.save()

    def _close(self) -> None:
        """关闭窗口"""
        if self.typing_job:
            self.window.after_cancel(self.typing_job)

        if self.on_close:
            self.on_close()

        self.window.destroy()
        self.window = None
