"""
chat_window.py - 小铁皮·学术日报窗口
暖色系卡片式设计，支持聊天记录、反馈、笔记功能
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Callable, Optional
from pathlib import Path

from .config import CHAT_HISTORY_FILE, SAVE_DIR
from .summarizer import PaperSummarizer
from .taste import TasteProfile

# ===== 路径常量 =====
NOTES_DIR = SAVE_DIR / 'notes'
BOOKMARKS_FILE = SAVE_DIR / 'bookmarks.json'


class BookmarkManager:
    """收藏管理器"""

    def __init__(self):
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        self.bookmarks = self._load()

    def _load(self) -> List[Dict]:
        """加载收藏"""
        if BOOKMARKS_FILE.exists():
            try:
                with open(BOOKMARKS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('bookmarks', [])
            except:
                pass
        return []

    def save(self) -> None:
        """保存收藏"""
        try:
            with open(BOOKMARKS_FILE, 'w', encoding='utf-8') as f:
                json.dump({'bookmarks': self.bookmarks}, f, ensure_ascii=False, indent=2)
        except:
            pass

    def add(self, paper: Dict) -> None:
        """添加收藏"""
        paper_id = paper.get('id', paper.get('title', ''))
        if not self.is_bookmarked(paper_id):
            self.bookmarks.insert(0, {
                'id': paper_id,
                'title': paper.get('title', 'Untitled'),
                'title_cn': paper.get('title_cn', ''),
                'url': paper.get('url', ''),
                'tags': paper.get('tags', []),
                'comment': paper.get('comment', ''),
                'interest_score': paper.get('interest_score', 3),
                'bookmarked_at': datetime.now().isoformat()
            })
            self.save()

    def remove(self, paper_id: str) -> None:
        """移除收藏"""
        self.bookmarks = [b for b in self.bookmarks if b['id'] != paper_id]
        self.save()

    def is_bookmarked(self, paper_id: str) -> bool:
        """是否已收藏"""
        return any(b['id'] == paper_id for b in self.bookmarks)

    def get_all(self) -> List[Dict]:
        """获取所有收藏"""
        return self.bookmarks

    def get_old_bookmarks(self, days: int = 3) -> List[Dict]:
        """获取超过指定天数未查看的收藏"""
        cutoff = datetime.now() - timedelta(days=days)
        old = []
        for b in self.bookmarks:
            try:
                bookmarked = datetime.fromisoformat(b['bookmarked_at'])
                if bookmarked < cutoff:
                    old.append(b)
            except:
                pass
        return old

# ===== 样式常量 =====
COLORS = {
    'border_outer': '#8B4513',
    'border_inner': '#CD853F',
    'bg_main': '#FFF5E6',
    'bg_card': '#FFFAF5',
    'bg_card_recommended': '#FFF0E0',
    'border_card': '#E8D5C4',
    'border_recommended': '#E07050',
    'text_primary': '#3E2723',
    'text_secondary': '#6D4C41',
    'text_link': '#CC3333',
    'star': '#FF9800',
    'star_empty': '#E0C8A8',
    'tag_bg': '#FFE0B2',
    'tag_text': '#E65100',
    'bg_input_area': '#FFE8CC',
    'bg_input': '#FFFFFF',
    'btn_send': '#A0522D',
    'btn_send_text': '#FFFFFF',
    'scrollbar': '#D2A679',
    'scrollbar_bg': '#F5E6D3',
    'user_bubble': '#F5E6D3',
    'copy_btn': '#D2B48C',
    'copy_btn_hover': '#C4A67C',
    'thumbs_up': '#27AE60',
    'thumbs_down': '#E74C3C',
    'btn_disabled': '#CCCCCC',
    'note_btn': '#8B7355',
}

FONTS = {
    'title': ('Helvetica', 13, 'bold'),
    'greeting': ('Helvetica', 10),
    'paper_title': ('Helvetica', 11, 'bold'),
    'body': ('Helvetica', 10),
    'comment': ('Helvetica', 10),
    'tag': ('Helvetica', 9),
    'small': ('Helvetica', 9),
    'input': ('Helvetica', 11),
}

# 小铁皮调色板
PET_COLORS = {
    0: None,
    1: '#D4856A',
    2: '#2D2D2D',
    3: '#B86E55',
    4: '#E8A08E',
}

# 小铁皮表情精灵图
EMOJI_SPRITES = {
    'happy': [
        [0, 1, 1, 0, 0, 0, 0, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 3, 3, 1, 1, 3, 3, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ],
    'idle': [
        [0, 1, 1, 0, 0, 0, 0, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 2, 2, 1, 1, 2, 2, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ],
    'blink': [
        [0, 1, 1, 0, 0, 0, 0, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 3, 3, 1, 1, 3, 3, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ],
    'sleepy': [
        [0, 0, 0, 0, 0, 3, 3, 1, 0, 0],
        [0, 0, 0, 0, 3, 1, 1, 1, 3, 0],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 1, 1, 3, 3, 1, 1, 1, 1],
        [0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
    ],
}

# 开场白
GREETINGS = {
    'normal': [
        "今天找到了 {count} 篇有意思的！",
        "来看看今天学术圈有什么新鲜事~",
        "论文已备好，请主人过目~",
    ],
    'excited': [
        "今天有篇特别厉害的！快看！",
        "这篇论文让我兴奋了好一会儿！",
        "今天的收获不错哦！",
    ],
    'few_papers': [
        "今天相关的论文不多，就这几篇",
        "安静的一天，只找到 {count} 篇",
    ],
    'no_papers': [
        "今天还没抓到论文呢…可能是网络问题",
        "论文库好像空空的…",
    ],
    'continue': [
        "欢迎回来~ 我们接着聊？",
        "又见面了！之前聊到哪了？",
    ],
}

WINDOW_WIDTH = 440
WINDOW_HEIGHT = 580
CARD_WIDTH = 380


class PaperChatWindow:
    """学术日报聊天窗口"""

    def __init__(self, parent: tk.Tk, papers: List[Dict], on_close: Callable = None,
                 save_manager=None):
        self.parent = parent
        self.papers = papers
        self.on_close = on_close
        self.save_manager = save_manager  # 用于增加亲密度
        self.summarizer = PaperSummarizer()
        self.taste_profile = TasteProfile()
        self.bookmark_manager = BookmarkManager()
        self.window = None
        self.placeholder_text = '想聊聊哪篇？'
        self._drag_data = {'x': 0, 'y': 0}

        # 聊天记录
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.history_data = self._load_history()
        self.today_conversations = self.history_data.get(self.today, {}).get('conversations', [])
        self.today_feedback = self.history_data.get(self.today, {}).get('feedback', {})

        # 如果今天有对话记录，标记所有论文为"已讨论"
        if self.today_conversations:
            self.papers_discussed = set(p.get('id', p.get('title', '')) for p in papers)
        else:
            self.papers_discussed = set()

        # 笔记本视图状态
        self.showing_notebook = False
        self.showing_bookmarks = False
        self.notebook_content_frame = None

    def show(self):
        """显示窗口"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title('小铁皮·学术日报')
        self.window.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')
        self.window.configure(bg=COLORS['border_outer'])
        self.window.resizable(True, True)
        self.window.minsize(360, 450)

        # macOS 无标题栏但支持输入
        try:
            self.window.wm_attributes('-topmost', True)
            self.window.tk.call('::tk::unsupported::MacWindowStyle', 'style',
                               self.window._w, 'plain', 'none')
        except:
            self.window.wm_attributes('-topmost', True)

        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._create_ui()
        self._populate_papers()
        self._load_today_conversations()
        self._position_window()
        self.window.after(100, self._fix_focus)

    # ===== 历史记录管理 =====

    def _load_history(self) -> Dict:
        """加载聊天历史"""
        if CHAT_HISTORY_FILE.exists():
            try:
                with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 兼容旧格式：移除旧的 'conversations' key
                if 'conversations' in data:
                    del data['conversations']

                return data
            except:
                pass
        return {}

    def _save_history(self):
        """保存聊天历史（使用临时文件+重命名，防止损坏）"""
        try:
            # 清理30天前的数据
            self._cleanup_old_history()

            # 更新今天的数据
            if self.today not in self.history_data:
                self.history_data[self.today] = {}

            self.history_data[self.today]['papers_shown'] = [p.get('id', '') for p in self.papers]
            self.history_data[self.today]['conversations'] = self.today_conversations
            self.history_data[self.today]['feedback'] = self.today_feedback

            # 写入临时文件然后重命名
            tmp_file = CHAT_HISTORY_FILE.with_suffix('.tmp')
            with open(tmp_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
            tmp_file.replace(CHAT_HISTORY_FILE)
        except Exception as e:
            print(f"Save history error: {e}")

    def _cleanup_old_history(self):
        """清理30天前的记录"""
        cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        self.history_data = {
            date: data for date, data in self.history_data.items()
            if date >= cutoff
        }

    def _save_conversation(self, user_msg: str, ai_response: str):
        """保存单条对话（每次对话后立即保存）"""
        now = datetime.now().strftime('%H:%M:%S')
        self.today_conversations.append({
            'time': now,
            'user': user_msg,
            'assistant': ai_response
        })
        self._save_history()

    def _load_today_conversations(self):
        """加载并显示今天的历史对话"""
        if self.today_conversations:
            for conv in self.today_conversations:
                self._add_message(conv['user'], is_user=True, save=False)
                self._add_message(conv['assistant'], is_user=False, save=False)

    # ===== UI 构建 =====

    def _fix_focus(self):
        """修复焦点问题"""
        try:
            self.window.focus_force()
            self.window.lift()
            self.window.bind('<Button-1>', self._on_window_click)
        except:
            pass

    def _on_window_click(self, event):
        """点击窗口时获取焦点"""
        if hasattr(self, 'input_entry') and event.widget == self.input_entry:
            self.input_entry.focus_set()

    def _position_window(self):
        """定位窗口"""
        try:
            pet_x = self.parent.winfo_x()
            pet_y = self.parent.winfo_y()
            screen_w = self.window.winfo_screenwidth()
            screen_h = self.window.winfo_screenheight()

            x = pet_x + 100
            y = pet_y - 200

            if x + WINDOW_WIDTH > screen_w:
                x = pet_x - WINDOW_WIDTH - 20
            if x < 0:
                x = 20
            if y + WINDOW_HEIGHT > screen_h:
                y = screen_h - WINDOW_HEIGHT - 50
            if y < 0:
                y = 50

            self.window.geometry(f'+{x}+{y}')
        except:
            pass

    def _create_ui(self):
        """创建UI"""
        outer_frame = tk.Frame(self.window, bg=COLORS['border_outer'])
        outer_frame.pack(fill='both', expand=True, padx=3, pady=3)

        inner_frame = tk.Frame(outer_frame, bg=COLORS['border_inner'])
        inner_frame.pack(fill='both', expand=True, padx=2, pady=2)

        self.main_frame = tk.Frame(inner_frame, bg=COLORS['bg_main'])
        self.main_frame.pack(fill='both', expand=True, padx=2, pady=2)

        self._build_header(self.main_frame)
        self._build_content_area(self.main_frame)
        self._build_input_area(self.main_frame)

    def _build_header(self, parent):
        """构建标题栏"""
        header_frame = tk.Frame(parent, bg=COLORS['bg_main'], height=70)
        header_frame.pack(fill='x', padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)

        header_frame.bind('<ButtonPress-1>', self._start_drag)
        header_frame.bind('<B1-Motion>', self._on_drag)

        top_row = tk.Frame(header_frame, bg=COLORS['bg_main'])
        top_row.pack(fill='x')
        top_row.bind('<ButtonPress-1>', self._start_drag)
        top_row.bind('<B1-Motion>', self._on_drag)

        # 小铁皮头像
        avatar_canvas = tk.Canvas(top_row, width=28, height=20,
                                  bg=COLORS['bg_main'], highlightthickness=0)
        avatar_canvas.pack(side='left', padx=(0, 8))
        self._draw_pet_emoji(avatar_canvas, 'idle', pixel_size=3)

        # 标题
        self.title_label = tk.Label(top_row, text='学术日报',
                                    font=FONTS['title'], fg=COLORS['text_primary'],
                                    bg=COLORS['bg_main'])
        self.title_label.pack(side='left')
        self.title_label.bind('<ButtonPress-1>', self._start_drag)
        self.title_label.bind('<B1-Motion>', self._on_drag)

        # 日期
        date_label = tk.Label(top_row, text=f'  {self.today}',
                             font=FONTS['small'], fg=COLORS['text_secondary'],
                             bg=COLORS['bg_main'])
        date_label.pack(side='left')

        # 关闭按钮
        close_btn = tk.Label(top_row, text='✕', font=('Helvetica', 14, 'bold'),
                            fg=COLORS['border_outer'], bg=COLORS['bg_main'], cursor='hand2')
        close_btn.pack(side='right', padx=5)
        close_btn.bind('<Button-1>', lambda e: self._on_close())
        close_btn.bind('<Enter>', lambda e: e.widget.config(fg='#C0392B'))
        close_btn.bind('<Leave>', lambda e: e.widget.config(fg=COLORS['border_outer']))

        # 笔记本按钮
        notebook_btn = tk.Label(top_row, text='📒', font=FONTS['title'],
                               fg=COLORS['note_btn'], bg=COLORS['bg_main'], cursor='hand2')
        notebook_btn.pack(side='right', padx=5)
        notebook_btn.bind('<Button-1>', lambda e: self._toggle_notebook())
        notebook_btn.bind('<Enter>', lambda e: e.widget.config(fg=COLORS['border_outer']))
        notebook_btn.bind('<Leave>', lambda e: e.widget.config(fg=COLORS['note_btn']))

        # 收藏列表按钮
        bookmark_btn = tk.Label(top_row, text='📚', font=FONTS['title'],
                               fg=COLORS['note_btn'], bg=COLORS['bg_main'], cursor='hand2')
        bookmark_btn.pack(side='right', padx=5)
        bookmark_btn.bind('<Button-1>', lambda e: self._toggle_bookmarks())
        bookmark_btn.bind('<Enter>', lambda e: e.widget.config(fg=COLORS['border_outer']))
        bookmark_btn.bind('<Leave>', lambda e: e.widget.config(fg=COLORS['note_btn']))

        # 开场白
        greeting_text = self._get_greeting()
        self.greeting_label = tk.Label(header_frame, text=greeting_text,
                                       font=FONTS['greeting'], fg=COLORS['text_secondary'],
                                       bg=COLORS['bg_main'], anchor='w')
        self.greeting_label.pack(fill='x', pady=(5, 0))

        # 分隔线
        separator = tk.Frame(parent, bg=COLORS['border_inner'], height=2)
        separator.pack(fill='x', padx=10, pady=5)

    def _build_content_area(self, parent):
        """构建可滚动内容区"""
        content_container = tk.Frame(parent, bg=COLORS['bg_main'])
        content_container.pack(fill='both', expand=True, padx=5)

        self.canvas = tk.Canvas(content_container, bg=COLORS['bg_main'], highlightthickness=0)

        style = ttk.Style()
        style.theme_use('default')
        style.configure('Custom.Vertical.TScrollbar',
                       background=COLORS['scrollbar'],
                       troughcolor=COLORS['scrollbar_bg'],
                       bordercolor=COLORS['scrollbar_bg'],
                       arrowcolor=COLORS['border_outer'])

        scrollbar = ttk.Scrollbar(content_container, orient='vertical',
                                  command=self.canvas.yview,
                                  style='Custom.Vertical.TScrollbar')

        self.content_frame = tk.Frame(self.canvas, bg=COLORS['bg_main'])
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor='nw')

        self.content_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
        self.content_frame.bind('<MouseWheel>', self._on_mousewheel)

    def _build_input_area(self, parent):
        """构建输入区"""
        self.input_container = tk.Frame(parent, bg=COLORS['bg_input_area'], height=55)
        self.input_container.pack(fill='x', side='bottom')
        self.input_container.pack_propagate(False)

        inner_padding = tk.Frame(self.input_container, bg=COLORS['bg_input_area'])
        inner_padding.pack(fill='both', expand=True, padx=10, pady=10)

        self.input_entry = tk.Entry(inner_padding, font=FONTS['input'],
                                    bg=COLORS['bg_input'], fg=COLORS['text_secondary'],
                                    insertbackground=COLORS['text_primary'], relief='flat',
                                    highlightthickness=2, highlightbackground=COLORS['border_card'],
                                    highlightcolor=COLORS['border_inner'])
        self.input_entry.pack(side='left', fill='both', expand=True, padx=(0, 8))
        self.input_entry.insert(0, self.placeholder_text)
        self.input_entry.bind('<FocusIn>', self._on_entry_focus_in)
        self.input_entry.bind('<FocusOut>', self._on_entry_focus_out)
        self.input_entry.bind('<Return>', self._on_send)
        self.input_entry.bind('<Button-1>', self._on_entry_click)

        send_btn = tk.Label(inner_padding, text='发送', font=FONTS['body'],
                           fg=COLORS['btn_send_text'], bg=COLORS['btn_send'],
                           padx=12, pady=6, cursor='hand2')
        send_btn.pack(side='right')
        send_btn.bind('<Button-1>', self._on_send)
        send_btn.bind('<Enter>', lambda e: e.widget.config(bg=COLORS['border_outer']))
        send_btn.bind('<Leave>', lambda e: e.widget.config(bg=COLORS['btn_send']))

    def _get_greeting(self) -> str:
        """获取开场白"""
        import random

        # 如果有历史对话，使用"继续"类型的开场白
        if self.today_conversations:
            return random.choice(GREETINGS['continue'])

        if not self.papers:
            return random.choice(GREETINGS['no_papers'])

        count = len(self.papers)
        has_high_score = any(p.get('interest_score', 0) >= 4 for p in self.papers)

        if count < 3:
            templates = GREETINGS['few_papers']
        elif has_high_score:
            templates = GREETINGS['excited']
        else:
            templates = GREETINGS['normal']

        return random.choice(templates).format(count=count)

    def _draw_pet_emoji(self, canvas: tk.Canvas, emotion: str, pixel_size: int = 2):
        """绘制小铁皮表情"""
        sprite = EMOJI_SPRITES.get(emotion, EMOJI_SPRITES['idle'])
        for r, row in enumerate(sprite):
            for c, val in enumerate(row):
                if val == 0:
                    continue
                color = PET_COLORS.get(val, '#D4856A')
                if color:
                    x1, y1 = c * pixel_size, r * pixel_size
                    x2, y2 = x1 + pixel_size, y1 + pixel_size
                    canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)

    def _get_emotion_for_score(self, score: int) -> str:
        """根据评分返回表情"""
        if score >= 5:
            return 'happy'
        elif score >= 3:
            return 'idle'
        elif score >= 2:
            return 'blink'
        else:
            return 'sleepy'

    # ===== 论文卡片 =====

    def _populate_papers(self):
        """填充论文卡片"""
        if not self.papers:
            self._add_message("今天还没有抓到论文呢...可能是网络问题", save=False)
            return

        deep_read = [p for p in self.papers if p.get('deep_read')]
        others = [p for p in self.papers if not p.get('deep_read')]

        for paper in deep_read:
            self._create_paper_card(paper, is_recommended=True)
        for paper in others:
            self._create_paper_card(paper, is_recommended=False)

        self.window.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _create_paper_card(self, paper: Dict, is_recommended: bool = False):
        """创建论文卡片"""
        paper_id = paper.get('id', paper.get('title', ''))

        card_outer = tk.Frame(self.content_frame, bg=COLORS['bg_main'])
        card_outer.pack(fill='x', padx=10, pady=5)

        if is_recommended:
            accent_bar = tk.Frame(card_outer, bg=COLORS['border_recommended'], width=4)
            accent_bar.pack(side='left', fill='y')

        bg_color = COLORS['bg_card_recommended'] if is_recommended else COLORS['bg_card']
        card = tk.Frame(card_outer, bg=bg_color,
                       highlightbackground=COLORS['border_card'], highlightthickness=1)
        card.pack(side='left', fill='x', expand=True)

        card_inner = tk.Frame(card, bg=bg_color)
        card_inner.pack(fill='x', padx=12, pady=10)

        # 精读推荐标语
        if is_recommended:
            rec_frame = tk.Frame(card_inner, bg=bg_color)
            rec_frame.pack(fill='x', pady=(0, 6))
            rec_avatar = tk.Canvas(rec_frame, width=16, height=12, bg=bg_color, highlightthickness=0)
            rec_avatar.pack(side='left', padx=(0, 5))
            self._draw_pet_emoji(rec_avatar, 'happy', pixel_size=2)
            tk.Label(rec_frame, text='这篇推荐精读！', font=FONTS['body'],
                    fg=COLORS['text_link'], bg=bg_color).pack(side='left')

        # 星级 + 标签
        top_row = tk.Frame(card_inner, bg=bg_color)
        top_row.pack(fill='x', pady=(0, 6))

        score = paper.get('interest_score', 3)
        stars_text = '★' * score + '☆' * (5 - score)
        tk.Label(top_row, text=stars_text, font=FONTS['body'],
                fg=COLORS['star'], bg=bg_color).pack(side='left')

        for tag in paper.get('tags', [])[:3]:
            tk.Label(top_row, text=tag, font=FONTS['tag'],
                    fg=COLORS['tag_text'], bg=COLORS['tag_bg'],
                    padx=6, pady=1).pack(side='left', padx=(6, 0))

        # 标题（可点击）
        title = paper.get('title', 'Untitled')
        url = paper.get('url', '')
        title_label = tk.Label(card_inner, text=title, font=FONTS['paper_title'],
                              fg=COLORS['text_link'], bg=bg_color,
                              wraplength=CARD_WIDTH - 40, justify='left', anchor='w',
                              cursor='hand2' if url else 'arrow')
        title_label.pack(fill='x', pady=(0, 8))

        if url:
            title_label.bind('<Button-1>', lambda e, u=url: self._open_link(u))
            title_label.bind('<Enter>', lambda e: e.widget.config(font=FONTS['paper_title'] + ('underline',)))
            title_label.bind('<Leave>', lambda e: e.widget.config(font=FONTS['paper_title']))

        # 点评
        comment = paper.get('comment', '')
        if comment:
            comment_frame = tk.Frame(card_inner, bg=bg_color)
            comment_frame.pack(fill='x', pady=(0, 6))

            emotion = self._get_emotion_for_score(score)
            emoji_canvas = tk.Canvas(comment_frame, width=20, height=14,
                                    bg=bg_color, highlightthickness=0)
            emoji_canvas.pack(side='left', anchor='n', padx=(0, 6), pady=2)
            self._draw_pet_emoji(emoji_canvas, emotion, pixel_size=2)

            tk.Label(comment_frame, text=comment, font=FONTS['comment'],
                    fg=COLORS['text_secondary'], bg=bg_color,
                    wraplength=CARD_WIDTH - 70, justify='left', anchor='w'
                    ).pack(side='left', fill='x', expand=True)

        # 按钮区
        btn_row = tk.Frame(card_inner, bg=bg_color)
        btn_row.pack(fill='x')

        # 检查是否讨论过这篇论文
        discussed = paper_id in self.papers_discussed

        # ☆ 收藏按钮
        is_bookmarked = self.bookmark_manager.is_bookmarked(paper_id)
        bookmark_text = '★' if is_bookmarked else '☆'
        bookmark_color = COLORS['star'] if is_bookmarked else COLORS['star_empty']
        bookmark_btn = tk.Label(btn_row, text=bookmark_text, font=FONTS['body'],
                               fg=bookmark_color, bg=bg_color, cursor='hand2')
        bookmark_btn.pack(side='right', padx=2)
        bookmark_btn.bind('<Button-1>', lambda e, p=paper, b=bookmark_btn:
                         self._toggle_bookmark(p, b))

        # 📝 笔记按钮
        note_btn = tk.Label(btn_row, text='📝', font=FONTS['small'],
                           fg=COLORS['note_btn'] if discussed else COLORS['btn_disabled'],
                           bg=bg_color, cursor='hand2' if discussed else 'arrow')
        note_btn.pack(side='right', padx=2)
        if discussed:
            note_btn.bind('<Button-1>', lambda e, p=paper: self._save_note(p))

        # 复制按钮
        copy_btn = tk.Label(btn_row, text='📋', font=FONTS['small'],
                           fg=COLORS['copy_btn'], bg=bg_color, cursor='hand2')
        copy_btn.pack(side='right', padx=2)
        copy_btn.bind('<Button-1>', lambda e, p=paper, b=copy_btn: self._copy_paper(p, b))

        # 👎 按钮
        feedback = self.today_feedback.get(paper_id)
        down_color = COLORS['thumbs_down'] if feedback == 'down' else COLORS['btn_disabled']
        down_btn = tk.Label(btn_row, text='👎', font=FONTS['small'],
                           fg=down_color, bg=bg_color,
                           cursor='hand2' if feedback != 'up' else 'arrow')
        down_btn.pack(side='right', padx=2)

        # 👍 按钮
        up_color = COLORS['thumbs_up'] if feedback == 'up' else COLORS['btn_disabled']
        up_btn = tk.Label(btn_row, text='👍', font=FONTS['small'],
                         fg=up_color, bg=bg_color,
                         cursor='hand2' if feedback != 'down' else 'arrow')
        up_btn.pack(side='right', padx=2)

        # 绑定反馈事件
        if feedback is None:
            up_btn.bind('<Button-1>', lambda e, p=paper, ub=up_btn, db=down_btn:
                       self._on_thumbs_up(p, ub, db))
            down_btn.bind('<Button-1>', lambda e, p=paper, ub=up_btn, db=down_btn:
                         self._on_thumbs_down(p, ub, db))

        # 绑定滚轮
        for w in [card, card_inner, title_label]:
            w.bind('<MouseWheel>', self._on_mousewheel)

    # ===== 反馈功能 =====

    def _on_thumbs_up(self, paper: Dict, up_btn: tk.Label, down_btn: tk.Label):
        """点击👍"""
        paper_id = paper.get('id', paper.get('title', ''))

        # 更新品味档案
        for tag in paper.get('tags', []):
            self.taste_profile.boost_tag(tag, amount=0.5)
        self.taste_profile.save()

        # 更新反馈记录
        self.today_feedback[paper_id] = 'up'
        self._save_history()

        # 增加亲密度
        if self.save_manager:
            self.save_manager.add_trust(0.25, 'paper')
            self.save_manager.save()

        # 更新UI
        up_btn.config(fg=COLORS['thumbs_up'], cursor='arrow')
        down_btn.config(fg=COLORS['btn_disabled'], cursor='arrow')

        # 解绑事件
        up_btn.unbind('<Button-1>')
        down_btn.unbind('<Button-1>')

        self._show_toast("已记住你喜欢这类论文~")

    def _on_thumbs_down(self, paper: Dict, up_btn: tk.Label, down_btn: tk.Label):
        """点击👎"""
        paper_id = paper.get('id', paper.get('title', ''))

        for tag in paper.get('tags', []):
            self.taste_profile.reduce_tag(tag, amount=0.3)
        self.taste_profile.save()

        self.today_feedback[paper_id] = 'down'
        self._save_history()

        down_btn.config(fg=COLORS['thumbs_down'], cursor='arrow')
        up_btn.config(fg=COLORS['btn_disabled'], cursor='arrow')

        up_btn.unbind('<Button-1>')
        down_btn.unbind('<Button-1>')

        self._show_toast("下次少推这类了")

    def _show_toast(self, message: str):
        """显示提示消息"""
        toast = tk.Toplevel(self.window)
        toast.overrideredirect(True)
        toast.wm_attributes('-topmost', True)

        label = tk.Label(toast, text=message, font=FONTS['body'],
                        fg=COLORS['btn_send_text'], bg=COLORS['btn_send'],
                        padx=15, pady=8)
        label.pack()

        # 定位到窗口中央
        self.window.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 200) // 2
        y = self.window.winfo_y() + self.window.winfo_height() - 100
        toast.geometry(f'+{x}+{y}')

        toast.after(1500, toast.destroy)

    # ===== 聊天功能 =====

    def _add_message(self, text: str, is_user: bool = False, save: bool = True):
        """添加聊天消息"""
        msg_frame = tk.Frame(self.content_frame, bg=COLORS['bg_main'])
        msg_frame.pack(fill='x', padx=10, pady=5)

        if is_user:
            bubble = tk.Label(msg_frame, text=text, font=FONTS['body'],
                             fg=COLORS['text_primary'], bg=COLORS['user_bubble'],
                             wraplength=CARD_WIDTH - 60, justify='left', padx=12, pady=8)
            bubble.pack(side='right')
        else:
            avatar_canvas = tk.Canvas(msg_frame, width=20, height=14,
                                     bg=COLORS['bg_main'], highlightthickness=0)
            avatar_canvas.pack(side='left', anchor='n', padx=(0, 8), pady=4)
            self._draw_pet_emoji(avatar_canvas, 'idle', pixel_size=2)

            bubble = tk.Label(msg_frame, text=text, font=FONTS['body'],
                             fg=COLORS['text_primary'], bg=COLORS['bg_card'],
                             wraplength=CARD_WIDTH - 60, justify='left', padx=12, pady=8,
                             highlightbackground=COLORS['border_card'], highlightthickness=1)
            bubble.pack(side='left')

        msg_frame.bind('<MouseWheel>', self._on_mousewheel)
        bubble.bind('<MouseWheel>', self._on_mousewheel)

        self.window.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.canvas.yview_moveto(1.0)

    def _on_send(self, event=None):
        """发送消息"""
        user_input = self.input_entry.get().strip()
        if not user_input or user_input == self.placeholder_text:
            return

        self.input_entry.delete(0, 'end')
        self._add_message(user_input, is_user=True, save=False)

        self.placeholder_text = '继续问？'
        self._add_message("让我想想...", is_user=False, save=False)

        def get_response():
            # 带上历史context
            response = self._chat_with_context(user_input)
            self.window.after(0, lambda: self._show_response(user_input, response))

        threading.Thread(target=get_response, daemon=True).start()

    def _chat_with_context(self, user_question: str) -> str:
        """带历史context的聊天"""
        # 构建历史消息（最多5轮）
        history = []
        for conv in self.today_conversations[-5:]:
            # 截断过长的消息
            user_msg = conv['user'][:500] + '...' if len(conv['user']) > 500 else conv['user']
            ai_msg = conv['assistant'][:500] + '...' if len(conv['assistant']) > 500 else conv['assistant']
            history.append({'role': 'user', 'content': user_msg})
            history.append({'role': 'assistant', 'content': ai_msg})

        return self.summarizer.chat(user_question, self.papers, history)

    def _show_response(self, user_msg: str, response: str):
        """显示AI回复"""
        # 移除"让我想想..."
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and child.cget('text') == '让我想想...':
                        widget.destroy()
                        break

        self._add_message(response, is_user=False, save=False)

        # 保存对话
        self._save_conversation(user_msg, response)

        # 标记讨论过的论文
        # 任何对话都算讨论过（因为上下文中包含了论文信息）
        # 用户只要提问了，就可以为任意论文生成笔记
        for paper in self.papers:
            self.papers_discussed.add(paper.get('id', paper.get('title', '')))

    # ===== 笔记功能 =====

    def _save_note(self, paper: Dict):
        """保存论文笔记"""
        paper_id = paper.get('id', paper.get('title', ''))
        title = paper.get('title', 'Untitled')
        url = paper.get('url', '')

        # 找出与这篇论文相关的对话
        related_convs = []
        title_words = set(title.lower().split()[:5])
        for conv in self.today_conversations:
            if any(word in conv['user'].lower() or word in conv['assistant'].lower()
                   for word in title_words):
                related_convs.append(conv)

        if not related_convs:
            self._show_toast("还没有关于这篇论文的讨论")
            return

        # 生成笔记内容
        self._show_toast("正在生成笔记...")

        def generate_and_save():
            try:
                # 构建对话文本
                conv_text = '\n'.join([
                    f"> 用户：{c['user']}\n> 小铁皮：{c['assistant']}"
                    for c in related_convs
                ])

                # 调用AI生成总结
                summary_prompt = f"""请根据以下对话，提取关于这篇论文的讨论要点。

论文标题：{title}

对话记录：
{conv_text}

请用简洁的要点形式总结：
- 论文的核心发现/方法
- 讨论中的重要理解或启发

用中文，3-6个要点就够，不要太长。只输出要点，不要其他内容。"""

                summary = self.summarizer.chat(summary_prompt, [], [])

                # 生成笔记内容
                note_content = f"""# {title}

论文链接: {url}
讨论日期: {self.today}

## 讨论要点

{summary}

## 原始对话

{conv_text}
"""

                # 保存文件
                NOTES_DIR.mkdir(parents=True, exist_ok=True)

                # 生成文件名
                safe_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)[:50].strip()
                safe_title = safe_title.replace(' ', '_').lower()
                filename = f"{safe_title}_{self.today}.txt"
                filepath = NOTES_DIR / filename

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(note_content)

                self.window.after(0, lambda: self._show_toast(f"笔记已保存~ 📝"))

            except Exception as e:
                self.window.after(0, lambda: self._show_toast(f"保存失败: {e}"))

        threading.Thread(target=generate_and_save, daemon=True).start()

    # ===== 笔记本查看器 =====

    def _toggle_notebook(self):
        """切换笔记本视图"""
        if self.showing_notebook:
            self._show_papers_view()
        elif self.showing_bookmarks:
            self._show_notebook_view()
        else:
            self._show_notebook_view()

    def _show_notebook_view(self):
        """显示笔记本视图"""
        self.showing_notebook = True
        self.showing_bookmarks = False
        self.title_label.config(text='论文笔记')
        self.greeting_label.config(text='')

        # 隐藏输入区
        self.input_container.pack_forget()

        # 清空内容区
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # 加载笔记
        notes = self._load_notes()

        if not notes:
            # 空状态
            empty_frame = tk.Frame(self.content_frame, bg=COLORS['bg_main'])
            empty_frame.pack(fill='both', expand=True, pady=50)

            tk.Label(empty_frame, text='📝', font=('Helvetica', 40),
                    bg=COLORS['bg_main']).pack()
            tk.Label(empty_frame, text='还没有笔记哦~',
                    font=FONTS['title'], fg=COLORS['text_secondary'],
                    bg=COLORS['bg_main']).pack(pady=10)
            tk.Label(empty_frame, text='和我聊聊论文，然后点 📝 保存吧',
                    font=FONTS['body'], fg=COLORS['text_secondary'],
                    bg=COLORS['bg_main']).pack()
        else:
            # 显示笔记列表
            for note in notes:
                self._create_note_card(note)

        self.window.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _show_papers_view(self):
        """返回论文视图"""
        self.showing_notebook = False
        self.showing_bookmarks = False
        self.title_label.config(text='学术日报')
        self.greeting_label.config(text=self._get_greeting())

        # 显示输入区
        self.input_container.pack(fill='x', side='bottom')

        # 清空并重新填充
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self._populate_papers()
        self._load_today_conversations()

    def _load_notes(self) -> List[Dict]:
        """加载所有笔记"""
        notes = []
        if not NOTES_DIR.exists():
            return notes

        for filepath in NOTES_DIR.glob('*.txt'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 解析标题和日期
                lines = content.split('\n')
                title = lines[0].lstrip('# ').strip() if lines else filepath.stem

                # 从文件名提取日期
                match = re.search(r'(\d{4}-\d{2}-\d{2})', filepath.stem)
                date = match.group(1) if match else ''

                # 提取链接
                url = ''
                for line in lines:
                    if line.startswith('论文链接:'):
                        url = line.replace('论文链接:', '').strip()
                        break

                notes.append({
                    'filepath': str(filepath),
                    'filename': filepath.name,
                    'title': title,
                    'date': date,
                    'url': url,
                    'content': content
                })
            except:
                continue

        # 按日期倒序
        return sorted(notes, key=lambda x: x['date'], reverse=True)

    def _create_note_card(self, note: Dict):
        """创建笔记卡片"""
        card = tk.Frame(self.content_frame, bg=COLORS['bg_card'],
                       highlightbackground=COLORS['border_card'], highlightthickness=1)
        card.pack(fill='x', padx=10, pady=5)

        card_inner = tk.Frame(card, bg=COLORS['bg_card'])
        card_inner.pack(fill='x', padx=12, pady=10)

        # 标题
        title_text = note['title'][:40] + '...' if len(note['title']) > 40 else note['title']
        title_label = tk.Label(card_inner, text=f"📄 {title_text}",
                              font=FONTS['paper_title'], fg=COLORS['text_link'],
                              bg=COLORS['bg_card'], anchor='w', cursor='hand2')
        title_label.pack(fill='x')
        title_label.bind('<Button-1>', lambda e, n=note: self._show_note_detail(n))

        # 日期
        tk.Label(card_inner, text=note['date'], font=FONTS['small'],
                fg=COLORS['text_secondary'], bg=COLORS['bg_card'],
                anchor='w').pack(fill='x')

        card.bind('<MouseWheel>', self._on_mousewheel)

    def _show_note_detail(self, note: Dict):
        """显示笔记详情"""
        # 清空内容区
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # 返回按钮
        back_frame = tk.Frame(self.content_frame, bg=COLORS['bg_main'])
        back_frame.pack(fill='x', padx=10, pady=5)

        back_btn = tk.Label(back_frame, text='← 返回列表', font=FONTS['body'],
                           fg=COLORS['text_link'], bg=COLORS['bg_main'], cursor='hand2')
        back_btn.pack(side='left')
        back_btn.bind('<Button-1>', lambda e: self._show_notebook_view())

        # 笔记内容卡片
        content_card = tk.Frame(self.content_frame, bg=COLORS['bg_card'],
                               highlightbackground=COLORS['border_card'], highlightthickness=1)
        content_card.pack(fill='both', expand=True, padx=10, pady=5)

        content_inner = tk.Frame(content_card, bg=COLORS['bg_card'])
        content_inner.pack(fill='both', expand=True, padx=12, pady=10)

        # 显示笔记内容
        content_label = tk.Label(content_inner, text=note['content'],
                                font=FONTS['body'], fg=COLORS['text_primary'],
                                bg=COLORS['bg_card'], wraplength=CARD_WIDTH - 40,
                                justify='left', anchor='nw')
        content_label.pack(fill='both', expand=True)

        # 按钮区
        btn_frame = tk.Frame(content_inner, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(10, 0))

        if note.get('url'):
            open_btn = tk.Label(btn_frame, text='打开原文', font=FONTS['small'],
                               fg=COLORS['btn_send_text'], bg=COLORS['btn_send'],
                               padx=8, pady=4, cursor='hand2')
            open_btn.pack(side='left', padx=(0, 5))
            open_btn.bind('<Button-1>', lambda e, u=note['url']: self._open_link(u))

        finder_btn = tk.Label(btn_frame, text='在Finder中显示', font=FONTS['small'],
                             fg=COLORS['btn_send_text'], bg=COLORS['note_btn'],
                             padx=8, pady=4, cursor='hand2')
        finder_btn.pack(side='left', padx=(0, 5))
        finder_btn.bind('<Button-1>', lambda e, p=note['filepath']: self._open_in_finder(p))

        delete_btn = tk.Label(btn_frame, text='删除', font=FONTS['small'],
                             fg=COLORS['btn_send_text'], bg=COLORS['thumbs_down'],
                             padx=8, pady=4, cursor='hand2')
        delete_btn.pack(side='left')
        delete_btn.bind('<Button-1>', lambda e, n=note: self._delete_note(n))

        content_card.bind('<MouseWheel>', self._on_mousewheel)
        self.window.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _open_in_finder(self, filepath: str):
        """在Finder中显示文件"""
        try:
            subprocess.run(['open', '-R', filepath])
        except:
            pass

    def _delete_note(self, note: Dict):
        """删除笔记"""
        if messagebox.askyesno('确认删除', f'确定要删除这条笔记吗？\n\n{note["title"]}'):
            try:
                os.remove(note['filepath'])
                self._show_toast("已删除")
                self._show_notebook_view()
            except Exception as e:
                self._show_toast(f"删除失败: {e}")

    # ===== 收藏功能 =====

    def _toggle_bookmark(self, paper: Dict, btn: tk.Label):
        """切换收藏状态"""
        paper_id = paper.get('id', paper.get('title', ''))

        if self.bookmark_manager.is_bookmarked(paper_id):
            self.bookmark_manager.remove(paper_id)
            btn.config(text='☆', fg=COLORS['star_empty'])
            self._show_toast("已取消收藏")
        else:
            self.bookmark_manager.add(paper)
            btn.config(text='★', fg=COLORS['star'])
            self._show_toast("已收藏~ ⭐")
            # 收藏时增加亲密度
            if self.save_manager:
                self.save_manager.add_trust(0.25, 'paper')
                self.save_manager.save()

    def _toggle_bookmarks(self):
        """切换收藏列表视图"""
        if self.showing_bookmarks:
            self._show_papers_view()
        else:
            self._show_bookmarks_view()

    def _show_bookmarks_view(self):
        """显示收藏列表视图"""
        self.showing_bookmarks = True
        self.showing_notebook = False

        bookmarks = self.bookmark_manager.get_all()
        count = len(bookmarks)
        self.title_label.config(text=f'我的收藏 ({count}篇)')
        self.greeting_label.config(text='')

        # 隐藏输入区
        self.input_container.pack_forget()

        # 清空内容区
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if not bookmarks:
            # 空状态
            empty_frame = tk.Frame(self.content_frame, bg=COLORS['bg_main'])
            empty_frame.pack(fill='both', expand=True, pady=50)

            tk.Label(empty_frame, text='⭐', font=('Helvetica', 40),
                    bg=COLORS['bg_main']).pack()
            tk.Label(empty_frame, text='还没有收藏哦~',
                    font=FONTS['title'], fg=COLORS['text_secondary'],
                    bg=COLORS['bg_main']).pack(pady=10)
            tk.Label(empty_frame, text='看到喜欢的论文，点 ☆ 收藏吧',
                    font=FONTS['body'], fg=COLORS['text_secondary'],
                    bg=COLORS['bg_main']).pack()
        else:
            # 显示收藏列表
            for bookmark in bookmarks:
                self._create_bookmark_card(bookmark)

        self.window.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _create_bookmark_card(self, bookmark: Dict):
        """创建收藏卡片"""
        card = tk.Frame(self.content_frame, bg=COLORS['bg_card'],
                       highlightbackground=COLORS['border_card'], highlightthickness=1)
        card.pack(fill='x', padx=10, pady=5)

        card_inner = tk.Frame(card, bg=COLORS['bg_card'])
        card_inner.pack(fill='x', padx=12, pady=10)

        # 星级
        score = bookmark.get('interest_score', 3)
        stars_text = '★' * score + '☆' * (5 - score)

        top_row = tk.Frame(card_inner, bg=COLORS['bg_card'])
        top_row.pack(fill='x')

        tk.Label(top_row, text=stars_text, font=FONTS['body'],
                fg=COLORS['star'], bg=COLORS['bg_card']).pack(side='left')

        # 标签
        for tag in bookmark.get('tags', [])[:2]:
            tk.Label(top_row, text=tag, font=FONTS['tag'],
                    fg=COLORS['tag_text'], bg=COLORS['tag_bg'],
                    padx=4, pady=1).pack(side='left', padx=(6, 0))

        # 标题（使用中文标题如果有的话）
        title = bookmark.get('title_cn') or bookmark.get('title', 'Untitled')
        title_display = title[:45] + '...' if len(title) > 45 else title
        url = bookmark.get('url', '')

        title_label = tk.Label(card_inner, text=title_display,
                              font=FONTS['paper_title'], fg=COLORS['text_link'],
                              bg=COLORS['bg_card'], anchor='w', wraplength=CARD_WIDTH - 50,
                              justify='left', cursor='hand2' if url else 'arrow')
        title_label.pack(fill='x', pady=(5, 0))

        if url:
            title_label.bind('<Button-1>', lambda e, u=url: self._open_link(u))

        # 收藏日期
        bookmarked_at = bookmark.get('bookmarked_at', '')
        if bookmarked_at:
            try:
                dt = datetime.fromisoformat(bookmarked_at)
                date_str = dt.strftime('%Y-%m-%d')
            except:
                date_str = ''
        else:
            date_str = ''

        if date_str:
            tk.Label(card_inner, text=f'收藏于 {date_str}', font=FONTS['small'],
                    fg=COLORS['text_secondary'], bg=COLORS['bg_card'],
                    anchor='w').pack(fill='x', pady=(2, 0))

        # 点评
        comment = bookmark.get('comment', '')
        if comment:
            comment_display = comment[:60] + '...' if len(comment) > 60 else comment
            tk.Label(card_inner, text=f'💬 {comment_display}', font=FONTS['small'],
                    fg=COLORS['text_secondary'], bg=COLORS['bg_card'],
                    anchor='w', wraplength=CARD_WIDTH - 60,
                    justify='left').pack(fill='x', pady=(4, 0))

        # 按钮区
        btn_frame = tk.Frame(card_inner, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(8, 0))

        # 打开原文按钮
        if url:
            open_btn = tk.Label(btn_frame, text='打开原文', font=FONTS['small'],
                               fg=COLORS['btn_send_text'], bg=COLORS['btn_send'],
                               padx=8, pady=3, cursor='hand2')
            open_btn.pack(side='left', padx=(0, 5))
            open_btn.bind('<Button-1>', lambda e, u=url: self._open_link(u))

        # 删除按钮
        delete_btn = tk.Label(btn_frame, text='取消收藏', font=FONTS['small'],
                             fg=COLORS['btn_send_text'], bg=COLORS['thumbs_down'],
                             padx=8, pady=3, cursor='hand2')
        delete_btn.pack(side='left')
        delete_btn.bind('<Button-1>', lambda e, b=bookmark: self._remove_bookmark(b))

        card.bind('<MouseWheel>', self._on_mousewheel)

    def _remove_bookmark(self, bookmark: Dict):
        """从收藏列表移除"""
        paper_id = bookmark.get('id', '')
        self.bookmark_manager.remove(paper_id)
        self._show_toast("已取消收藏")
        self._show_bookmarks_view()  # 刷新列表

    # ===== 工具方法 =====

    def _copy_paper(self, paper: Dict, button: tk.Label):
        """复制论文信息"""
        text = f"{paper.get('title', '')}\n{paper.get('url', '')}"
        self.window.clipboard_clear()
        self.window.clipboard_append(text)
        original_text = button.cget('text')
        button.config(text='✓', fg='#27AE60')
        button.after(800, lambda: button.config(text=original_text, fg=COLORS['copy_btn']))

    def _open_link(self, url: str):
        """打开链接"""
        try:
            webbrowser.open(url)
        except:
            pass

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-event.delta), 'units')

    def _on_entry_click(self, event):
        self.window.focus_force()
        self.input_entry.focus_set()

    def _on_entry_focus_in(self, event):
        if self.input_entry.get() == self.placeholder_text:
            self.input_entry.delete(0, 'end')
            self.input_entry.config(fg=COLORS['text_primary'])

    def _on_entry_focus_out(self, event):
        if not self.input_entry.get():
            self.input_entry.insert(0, self.placeholder_text)
            self.input_entry.config(fg=COLORS['text_secondary'])

    def _start_drag(self, event):
        self._drag_data['x'] = event.x
        self._drag_data['y'] = event.y

    def _on_drag(self, event):
        x = self.window.winfo_x() + (event.x - self._drag_data['x'])
        y = self.window.winfo_y() + (event.y - self._drag_data['y'])
        self.window.geometry(f'+{x}+{y}')

    def _on_close(self):
        """关闭窗口"""
        self._save_history()
        if self.on_close:
            self.on_close()
        if self.window:
            self.window.destroy()
            self.window = None
