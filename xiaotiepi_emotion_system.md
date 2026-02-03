# 😠😢 小铁皮 · 情绪系统重构 — Claude Code 任务说明

## 📋 任务概述

重构小铁皮的情绪系统，将**生气**和**难过**分开为两个独立的情绪维度，并完善生气-冷战-和好的完整闭环。

### 当前问题

1. 生气系统是独立的，没有和心情系统形成闭环
2. "生气"和"难过"混在一起，但它们是完全不同的情绪
3. SPRITE_SUPER_ANNOYED 画好了但没有使用
4. 没有"和好"机制，生气了不知道怎么解除

### 设计目标

- 生气和难过是**两个独立维度**，可以叠加
- 生气有完整的**冷战-和好**闭环
- 超级不爽需要玩家**输入"对不起"**才能和好
- 不同情绪状态有不同的视觉和交互表现

---

## 🎭 一、情绪双维度设计

### 1.1 两种情绪的区别

| | 生气 (Anger) | 难过 (Sadness) |
|---|---|---|
| **性质** | 外向的，针对用户 | 内向的，自己的状态 |
| **触发** | 被惹怒（点太多、摇晃、深夜打扰） | 被忽视（心情低、饿、脏、寂寞） |
| **表现** | 冷战、不理人、"哼！" | 丧、没精神、"唉..." |
| **视觉** | SPRITE_ANGRY / SPRITE_SUPER_ANNOYED | SPRITE_SAD |
| **解决** | 道歉 / 喂食安抚 / 等待 | 关心照顾（喂食、玩耍、陪伴） |

### 1.2 数据结构

```python
# 情绪状态（两个独立维度）
self.data = {
    # 生气维度
    'anger_level': 0,                    # 0=不生气, 1=轻微生气, 2=生气, 3=超级不爽
    'anger_cooldown': 0,                 # 冷战剩余时间（秒）
    'anger_click_count': 0,              # 滑动窗口内点击次数
    'anger_click_window_start': None,    # 点击计数窗口开始时间
    'anger_shake_count': 0,              # 摇晃次数
    'anger_last_shake_time': None,       # 上次摇晃时间
    'night_disturb_count': 0,            # 今晚深夜打扰次数
    'night_disturb_date': None,          # 记录是哪一晚
    
    # 心情维度（使用现有的 happiness，不要用 mood）
    'happiness': 80,                     # 0-100，影响难过状态
    
    # 组合状态
    'emotion_state': 'normal',           # 最终显示的情绪状态
}
```

**重要命名约定**：代码中统一使用 `happiness`，不要用 `mood`，保持和现有代码一致。

### 1.3 时间窗口和计数重置规则

**点击计数 - 10 分钟滑动窗口**：
```python
def _add_click_count(self):
    """增加点击计数（带时间窗口）"""
    now = time.time()
    window_start = self.data.get('anger_click_window_start')
    
    # 如果窗口不存在或超过 10 分钟，重置
    if window_start is None or (now - window_start) > 600:  # 600秒 = 10分钟
        self.data['anger_click_count'] = 1
        self.data['anger_click_window_start'] = now
    else:
        self.data['anger_click_count'] += 1
```

**摇晃计数 - 30 秒无摇晃自动重置**：
```python
def _add_shake_count(self):
    """增加摇晃计数"""
    now = time.time()
    last_shake = self.data.get('anger_last_shake_time')
    
    # 超过 30 秒没摇晃，重置计数
    if last_shake is None or (now - last_shake) > 30:
        self.data['anger_shake_count'] = 1
    else:
        self.data['anger_shake_count'] += 1
    
    self.data['anger_last_shake_time'] = now

def _reset_anger_counts(self):
    """触发生气后重置计数"""
    self.data['anger_click_count'] = 0
    self.data['anger_click_window_start'] = None
    self.data['anger_shake_count'] = 0
    self.data['anger_last_shake_time'] = None
```

### 1.4 情绪状态矩阵

根据 `anger_level` 和 `happiness` 组合判定 `emotion_state`：

```python
def _update_emotion_state(self):
    """根据生气程度和心情值判定当前情绪状态"""
    anger = self.data['anger_level']
    happiness = self.data['happiness']  # 注意：用 happiness 不是 mood
    
    # 生气优先级最高（因为这是针对用户的即时反应）
    if anger >= 3:
        self.data['emotion_state'] = 'super_annoyed'  # 超级不爽
    elif anger >= 2:
        self.data['emotion_state'] = 'angry'          # 生气
    elif anger >= 1:
        self.data['emotion_state'] = 'annoyed'        # 轻微不满
    # 然后看心情
    elif happiness <= 15:
        self.data['emotion_state'] = 'very_sad'       # 非常难过
    elif happiness <= 30:
        self.data['emotion_state'] = 'sad'            # 难过
    elif happiness >= 70 and self._all_needs_satisfied():
        self.data['emotion_state'] = 'happy'          # 开心
    else:
        self.data['emotion_state'] = 'normal'         # 普通
```

---

## 😠 二、生气系统完整设计

### 2.1 生气等级

**重要：生气机制只在工作时间触发（周一到周五 9:00-18:00）**

周末和下班时间点击/摇晃不会触发生气，毕竟休息日嘛。

```python
def _is_work_time(self):
    """检查是否在工作时间"""
    now = datetime.now()
    weekday = now.weekday()  # 0=周一, 6=周日
    hour = now.hour
    return weekday < 5 and 9 <= hour < 18
```

| 等级 | 名称 | 触发条件 | 视觉 | 
|------|------|---------|------|
| 0 | 正常 | 默认状态 | 普通精灵 |
| 1 | 轻微不满 | 工作时间点击 21-35 次 / 深夜第一次打扰 | SPRITE_ANGRY + 说"别戳了..." |
| 2 | 生气 | 工作时间点击 36-50 次 / 摇晃 4 次 / 深夜第二次打扰 | SPRITE_ANGRY + 冷战 30 秒 |
| 3 | 超级不爽 | 工作时间点击 50+ 次 / 摇晃 6+ 次 / 深夜打扰 3+ 次 / 生气时继续惹 | SPRITE_SUPER_ANNOYED + 冷战 2 分钟 |

### 2.2 深夜打扰机制

深夜时段：23:00 - 6:00

```python
def _handle_night_disturb(self):
    """处理深夜打扰"""
    now = datetime.now()
    hour = now.hour
    today = now.strftime('%Y-%m-%d')
    
    # 检查是否是深夜
    if not (hour >= 23 or hour < 6):
        return
    
    # 检查是否是新的一晚（重置计数）
    if self.data.get('night_disturb_date') != today:
        self.data['night_disturb_date'] = today
        self.data['night_disturb_count'] = 0
    
    self.data['night_disturb_count'] += 1
    count = self.data['night_disturb_count']
    
    # 根据打扰次数决定生气等级
    if count == 1:
        self._trigger_anger(level=1)
        self.show_bubble("唔...困...别吵...")
        self._adjust_happiness(-3)
    elif count == 2:
        self._trigger_anger(level=2)
        self.show_bubble("都说了在睡觉！")
        self._adjust_happiness(-5)
    else:  # 3+ 次
        self._trigger_anger(level=3)
        self.show_bubble("！！！不睡觉了是吧！！")
        self._adjust_happiness(-10)
```

### 2.3 冷战机制

```python
def _enter_cold_war(self, anger_level):
    """进入冷战状态"""
    if anger_level == 2:
        self.data['anger_cooldown'] = 30      # 30 秒冷战
        self.data['anger_level'] = 2
        self._adjust_happiness(-5)
        self.show_bubble("哼，不想理你")
    elif anger_level == 3:
        self.data['anger_cooldown'] = 120     # 2 分钟冷战
        self.data['anger_level'] = 3
        self._adjust_happiness(-15)
        self.show_bubble("生气了！！不理你了！！")
        # 超级不爽时弹出道歉输入框
        self._show_apology_dialog()
    
    self._update_emotion_state()

def _cold_war_tick(self):
    """冷战倒计时（每秒调用）"""
    if self.data['anger_cooldown'] > 0:
        self.data['anger_cooldown'] -= 1
        
        # 冷战期间每分钟心情 -2
        if self.data['anger_cooldown'] % 60 == 0:
            self._adjust_happiness(-2)
        
        # 冷战期间随机说话
        if random.random() < 0.02:  # 2% 概率
            phrases = ["...", "哼", "还在生气", "不想说话"]
            self.show_bubble(random.choice(phrases))
        
        # 超级不爽不会自动解除，必须道歉
        if self.data['anger_cooldown'] <= 0 and self.data['anger_level'] < 3:
            self._calm_down()

def _calm_down(self):
    """消气"""
    self.data['anger_level'] = 0
    self.data['anger_cooldown'] = 0
    self._reset_anger_counts()  # 重置所有计数
    self.show_bubble("好吧...原谅你了")
    self._adjust_happiness(+5)
    self._update_emotion_state()
```

### 2.3 冷战期间的交互响应

**关键：冷战只影响点击响应，右键菜单仍然可用！**

这样用户还可以通过右键菜单喂食/清洁来安抚小铁皮。

```python
def _on_click(self):
    """点击响应"""
    anger = self.data['anger_level']
    
    # 超级不爽：完全不响应点击
    if anger >= 3:
        if random.random() < 0.3:
            self.show_bubble("...")
        return
    
    # 生气中：响应但不给正面反馈
    if anger >= 2:
        responses = ["别碰我", "还在生气", "哼"]
        self.show_bubble(random.choice(responses))
        return
    
    # 轻微不满：警告
    if anger >= 1:
        self.show_bubble("别戳了啦...")
        self._add_click_count()
        return
    
    # 正常状态：正常响应
    self._normal_click_response()
    self._add_click_count()

def _on_right_click(self):
    """右键菜单 - 冷战期间仍然可用"""
    # 显示菜单：喂食、清洁、玩耍等
    # 冷战期间喂食可以减少冷战时间
    self._show_context_menu()

def _feed_during_cold_war(self):
    """冷战期间喂食 - 可以安抚"""
    if self.data['anger_level'] == 2:
        # 普通生气：喂食减少 10 秒冷战时间
        self.data['anger_cooldown'] = max(0, self.data['anger_cooldown'] - 10)
        self.show_bubble("哼...吃还是要吃的")
    elif self.data['anger_level'] == 3:
        # 超级不爽：喂食不能直接解除，但可以让小铁皮态度软化一点
        self.show_bubble("...你以为喂我就没事了？")
        # 不减少冷战时间，但记录喂食次数，累计 3 次后提示可以道歉了
```

### 2.4 和好机制

**普通生气（等级 2）的和好方式：**
- 等待 30 秒冷战期结束，自动和好
- 或者喂食安抚，每次喂食冷战时间 -10 秒

**超级不爽（等级 3）的和好方式：**
- 冷战期**不会自动结束**
- 必须在输入框输入"**对不起**"才能和好

```python
def _check_apology(self, user_input):
    """检查用户是否道歉"""
    apology_words = ['对不起', '抱歉', '我错了', 'sorry', '对不起啦', '原谅我']
    
    if self.data['anger_level'] >= 3:
        for word in apology_words:
            if word in user_input.lower():
                self._accept_apology()
                return True
    return False

def _accept_apology(self):
    """接受道歉"""
    self.data['anger_level'] = 0
    self.data['anger_cooldown'] = 0
    self._reset_anger_counts()
    self.show_bubble("...好吧，这次原谅你了 😤")
    self._adjust_happiness(+10)
    self._update_emotion_state()
```

### 2.5 道歉输入框（超级不爽时自动弹出）

当小铁皮进入超级不爽状态时，自动弹出一个小输入框让用户道歉：

```python
def _show_apology_dialog(self):
    """显示道歉输入框"""
    # 创建一个小的 Toplevel 窗口
    self.apology_dialog = tk.Toplevel(self.root)
    self.apology_dialog.title("")
    self.apology_dialog.overrideredirect(True)  # 无边框
    self.apology_dialog.attributes('-topmost', True)
    
    # 定位在小铁皮上方
    pet_x, pet_y = self.root.winfo_x(), self.root.winfo_y()
    self.apology_dialog.geometry(f"+{pet_x}+{pet_y - 80}")
    
    # 样式
    frame = tk.Frame(self.apology_dialog, bg='#FFF5E6', 
                     highlightbackground='#CD853F', highlightthickness=2)
    frame.pack(fill='both', expand=True, padx=2, pady=2)
    
    # 提示文字
    label = tk.Label(frame, text="小铁皮在生气...说点什么？", 
                    bg='#FFF5E6', fg='#3E2723', font=('Helvetica', 10))
    label.pack(padx=10, pady=(10, 5))
    
    # 输入框
    self.apology_entry = tk.Entry(frame, width=20, font=('Helvetica', 11))
    self.apology_entry.pack(padx=10, pady=(0, 10))
    self.apology_entry.bind('<Return>', self._on_apology_submit)
    self.apology_entry.focus_set()

def _on_apology_submit(self, event=None):
    """处理道歉输入"""
    text = self.apology_entry.get().strip()
    if self._check_apology(text):
        # 道歉成功，关闭对话框
        self.apology_dialog.destroy()
        self.apology_dialog = None
    else:
        # 道歉不对，提示
        self.apology_entry.delete(0, tk.END)
        self.show_bubble("哼，不是这样说的！")
```

### 2.6 输入框处理

在学术日报的输入框（或主界面如果有输入的话）检测道歉：

```python
def _on_user_input(self, text):
    """处理用户输入"""
    # 先检查是否是道歉
    if self._check_apology(text):
        return  # 道歉成功，不继续处理
    
    # 如果在超级不爽状态，不处理其他输入
    if self.data['anger_level'] >= 3:
        self.show_bubble("先跟我道歉！")
        return
    
    # 正常处理论文问题等
    self._process_normal_input(text)
```

---

## 😢 三、难过系统

### 3.1 难过的触发

难过是由**心情值 (happiness)** 驱动的，不是即时触发：

| 心情范围 | 状态 | 表现 |
|---------|------|------|
| 70+ | 开心 | 活泼、主动说话、走路蹦跳 |
| 31-69 | 普通 | 正常 |
| 16-30 | 难过 | 没精神、说丧气话、走路慢 |
| 0-15 | 非常难过 | 趴着不动、"不想动..."、需要很多关心 |

### 3.2 难过时的表现

```python
SAD_PHRASES = [
    "唉...",
    "有点难过",
    "你是不是忘了我...",
    "好无聊啊",
    "肚子饿...",
]

VERY_SAD_PHRASES = [
    "...",
    "不想动",
    "你还在吗...",
    "是不是不要我了",
]

def _sad_behavior(self):
    """难过时的行为"""
    if self.data['emotion_state'] == 'very_sad':
        # 非常难过：趴着不动
        self._set_sprite('SPRITE_LONELY')  # 用 LONELY 代替 SAD
        if random.random() < 0.01:
            self.show_bubble(random.choice(VERY_SAD_PHRASES))
    elif self.data['emotion_state'] == 'sad':
        # 难过：偶尔叹气
        self._set_sprite('SPRITE_LONELY')
        if random.random() < 0.02:
            self.show_bubble(random.choice(SAD_PHRASES))
```

### 3.3 难过的解除

难过通过**照顾**解除（和生气的"道歉"不同）：

```python
def _care_for_pet(self, action):
    """照顾宠物"""
    if action == 'feed':
        self._adjust_happiness(+5)
    elif action == 'play':
        self._adjust_happiness(+25)
    elif action == 'clean':
        self._adjust_happiness(+5)
    elif action == 'pet':  # 摸头
        self._adjust_happiness(+2)
        if self.data['emotion_state'] in ['sad', 'very_sad']:
            self.show_bubble("谢谢你陪我...")
    
    self._update_emotion_state()
```

---

## 🎨 四、视觉状态对应

### 4.1 精灵图使用

**注意**：代码中没有专门的 SPRITE_SAD，使用 **SPRITE_LONELY** 代替。

| 情绪状态 | 使用的精灵图 | 优先级 |
|---------|-------------|-------|
| super_annoyed | SPRITE_SUPER_ANNOYED | 1（最高） |
| angry | SPRITE_ANGRY | 2 |
| annoyed | SPRITE_ANGRY（复用） | 3 |
| very_sad | SPRITE_LONELY（复用） | 4 |
| sad | SPRITE_LONELY（复用） | 5 |
| happy | SPRITE_HAPPY | 6 |
| normal | SPRITE_IDLE | 7（最低） |

### 4.2 状态切换

```python
def _update_sprite_for_emotion(self):
    """根据情绪状态更新精灵图"""
    state = self.data['emotion_state']
    
    # 注意：sad 和 very_sad 用 SPRITE_LONELY
    sprite_map = {
        'super_annoyed': 'SPRITE_SUPER_ANNOYED',
        'angry': 'SPRITE_ANGRY',
        'annoyed': 'SPRITE_ANGRY',
        'very_sad': 'SPRITE_LONELY',  # 用 LONELY 代替 SAD
        'sad': 'SPRITE_LONELY',       # 用 LONELY 代替 SAD
        'happy': 'SPRITE_HAPPY',
        'normal': 'SPRITE_IDLE',
    }
    
    self._set_sprite(sprite_map.get(state, 'SPRITE_IDLE'))
```

---

## 🔄 五、完整状态流转图

```
                            ┌─────────────────┐
                            │     正常状态     │
                            │  emotion=normal │
                            └────────┬────────┘
                                     │
                ┌────────────────────┼────────────────────┐
                │                    │                    │
                ▼                    ▼                    ▼
    ┌───────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │    被惹怒触发      │  │   心情自然下降   │  │   被好好照顾     │
    │ (点击/摇晃/深夜)   │  │   (被忽视)      │  │                 │
    └─────────┬─────────┘  └────────┬────────┘  └────────┬────────┘
              │                     │                    │
              ▼                     ▼                    ▼
    ┌───────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │      生气         │  │     难过        │  │      开心       │
    │  emotion=angry    │  │  emotion=sad    │  │  emotion=happy  │
    │  [冷战 30 秒]     │  │                 │  │                 │
    └─────────┬─────────┘  └────────┬────────┘  └─────────────────┘
              │                     │
    ┌─────────┴─────────┐           │
    │  继续惹 / 摇晃    │           │
    └─────────┬─────────┘           │
              ▼                     │
    ┌───────────────────┐           │
    │    超级不爽       │           │
    │ emotion=super_    │           │
    │    annoyed        │           │
    │ [冷战 2 分钟]     │           │
    │ [需要道歉]        │           │
    └─────────┬─────────┘           │
              │                     │
              │  输入"对不起"        │  喂食/玩耍/陪伴
              ▼                     ▼
    ┌───────────────────────────────────────────┐
    │              恢复正常                      │
    │      anger_level=0, happiness 回升        │
    └───────────────────────────────────────────┘
```

---

## ⚠️ 六、注意事项

1. **生气和难过可以叠加**：比如又气又难过（被惹怒后又被忽视），但视觉上生气优先显示
2. **冷战期间心情会持续下降**：这是对玩家的惩罚，鼓励尽快道歉
3. **超级不爽必须道歉**：这是硬性要求，倒计时结束也不会自动和好
4. **道歉检测要宽容**：接受"对不起"、"抱歉"、"sorry"等多种写法
5. **状态持久化**：生气状态和冷战时间要保存到文件，程序重启后继续

---

## 🧪 七、验收标准

**生气系统：**
- [ ] **只在工作时间触发**（周一到周五 9:00-18:00），周末点击不生气
- [ ] 工作时间点击 21-35 次触发轻微不满，显示 SPRITE_ANGRY
- [ ] 工作时间点击 36-50 次触发生气，进入 30 秒冷战
- [ ] 工作时间点击 50+ 次触发超级不爽，显示 SPRITE_SUPER_ANNOYED，进入 2 分钟冷战
- [ ] 摇晃 4 次触发生气，摇晃 6+ 次触发超级不爽
- [ ] **10 分钟**无点击后计数重置
- [ ] **30 秒**无摇晃后摇晃计数重置

**深夜打扰：**
- [ ] 深夜（23:00-6:00）第一次打扰：level 1
- [ ] 同一晚第二次打扰：level 2
- [ ] 同一晚第三次+打扰：level 3
- [ ] 新的一晚重置打扰计数

**冷战机制：**
- [ ] 冷战期间点击不给正面反馈
- [ ] 冷战期间**右键菜单仍然可用**（可以喂食）
- [ ] 冷战期间喂食可以减少冷战时间（普通生气 -10 秒）
- [ ] 冷战期间显示"..."、"哼"等
- [ ] 冷战期间心情持续下降
- [ ] 普通生气 30 秒后自动和好
- [ ] 超级不爽**不会**自动和好

**道歉机制：**
- [ ] 超级不爽时**自动弹出道歉输入框**
- [ ] 输入"对不起"/"抱歉"/"sorry"等可以和好
- [ ] 道歉不对时提示"哼，不是这样说的！"
- [ ] 和好后显示"...好吧，这次原谅你了"
- [ ] 和好后心情 +10

**难过系统：**
- [ ] 心情 < 30 时显示 **SPRITE_LONELY**（代替 SAD）
- [ ] 难过时说丧气话
- [ ] 喂食/玩耍可以提升心情，解除难过
- [ ] 难过和生气是独立的，可以同时存在（但生气优先显示）

**命名一致性：**
- [ ] 代码中使用 `happiness` 而不是 `mood`
- [ ] 代码中使用 `SPRITE_LONELY` 代替 `SPRITE_SAD`
