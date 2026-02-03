"""
save.py - 小铁皮的数据持久化模块
保存/加载宠物状态到 ~/.xiaotiepi/save.json
"""

import json
import os
import time
from typing import Dict, Any, Optional, Tuple
import random
from pathlib import Path


SAVE_DIR = Path.home() / '.xiaotiepi'
SAVE_FILE = SAVE_DIR / 'save.json'

# 默认初始值
DEFAULT_DATA: Dict[str, Any] = {
    'hunger': 80,
    'cleanliness': 80,
    'happiness': 80,
    'vitality': 50,
    'alive_days': 0,
    'evolution_stage': 1,
    'is_dead': False,
    'sick_since': None,
    'last_save_time': None,
    'click_history': {},
    'hourly_clicks': {},
    'last_interaction': None,
    'created_at': None,
    'hunger_history': [],
    'body_type': 'normal',
    # 信任度系统
    'trust': 50,
    'trust_streak': 0,
    'last_trust_check_date': None,
    # 心情历史
    'mood_history': {
        'last_full_service_hour': None,
        'morning_greeted_today': False,
        'comfort_last_used': None,
        'services_this_hour': [],
    },
    # 睡眠数据
    'sleep_data': {
        'disturb_count_tonight': 0,
        'had_bad_sleep': False,
        'pre_sleep_mood': 70,
    },
    # 每日状态（跨天检测用）
    'daily_state': {
        'last_active_date': None,
        'greeted_today': False,
        'papers_fetched_today': False,
        'dream_settled_today': False,
        'last_dream': None,  # 'good', 'nightmare', 'none'
        'comforted_after_nightmare': False,
    },
    # 情绪系统（生气维度）
    'emotion': {
        'anger_level': 0,                    # 0=不生气, 1=轻微生气, 2=生气, 3=超级不爽
        'anger_cooldown': 0,                 # 冷战剩余时间（秒）
        'anger_click_count': 0,              # 滑动窗口内点击次数
        'anger_click_window_start': None,    # 点击计数窗口开始时间
        'anger_shake_count': 0,              # 摇晃次数
        'anger_last_shake_time': None,       # 上次摇晃时间
        'night_disturb_count': 0,            # 今晚深夜打扰次数
        'night_disturb_date': None,          # 记录是哪一晚
        'cold_war_feed_count': 0,            # 冷战期间喂食次数
        'emotion_state': 'normal',           # 最终显示的情绪状态
    },
}

# 摸鱼检测阈值
FISHING_THRESHOLD = 20      # 每小时点击超过20次判定为摸鱼
LONELY_HOURS_BASE = 3       # 基础寂寞阈值（信任度会延长）

# 心情相关常量
MOOD_CLICK_BONUS = (1, 2)       # 点击心情增益范围
MOOD_FULL_FEED_BONUS = 5        # 喂饱额外奖励
MOOD_CLEAN_BONUS = 5            # 洗净额外奖励
MOOD_FULL_SERVICE_BONUS = 10    # 全套服务奖励
MOOD_MORNING_BONUS = 3          # 早安奖励
MOOD_RANDOM_EVENT_BONUS = (3, 5)  # 随机开心事件
MOOD_SHAKE_PENALTY = -10        # 被晃晕
MOOD_SUPER_ANGRY_PENALTY = -20  # 超级生气
MOOD_NIGHT_DISTURB_FIRST = -3   # 深夜第一次打扰
MOOD_NIGHT_DISTURB_AFTER = -5   # 深夜后续打扰
MOOD_COMFORT_AMOUNT = 15        # 安慰恢复量
COMFORT_COOLDOWN = 1800         # 安慰冷却30分钟

# 情绪系统常量
ANGER_CLICK_WINDOW = 600        # 点击计数窗口（10分钟）
ANGER_SHAKE_RESET_TIME = 30     # 摇晃计数重置时间（30秒）
ANGER_CLICK_THRESHOLDS = {
    1: 21,   # 21-35 次 → 轻微不满
    2: 36,   # 36-50 次 → 生气
    3: 51,   # 51+ 次 → 超级不爽
}
ANGER_SHAKE_THRESHOLDS = {
    2: 4,    # 4 次 → 生气
    3: 6,    # 6+ 次 → 超级不爽
}
COLD_WAR_DURATION = {
    2: 30,   # 生气：30 秒冷战
    3: 120,  # 超级不爽：2 分钟冷战
}
ANGER_HAPPINESS_PENALTY = {
    1: -3,   # 轻微不满
    2: -5,   # 生气
    3: -15,  # 超级不爽
}
CALM_DOWN_HAPPINESS_BONUS = 5   # 和好后心情 +5
APOLOGY_HAPPINESS_BONUS = 10    # 道歉后心情 +10

# 信任度常量
TRUST_DAILY_GOOD = 2            # 每日照顾好+2
TRUST_STREAK_3_BONUS = 3        # 连续3天+3
TRUST_STREAK_7_BONUS = 5        # 连续7天+5
TRUST_ZERO_PENALTY = -5         # 数值归零-5
TRUST_DEATH_PENALTY = -20       # 死亡-20
TRUST_NEGLECT_PENALTY = -3      # 连续2天不照顾-3/天

# 数值衰减速率（每小时）
DECAY_RATES: Dict[str, float] = {
    'hunger': 5.0,      # 饥饿值每小时 -5
    'cleanliness': 3.0, # 清洁度每小时 -3
    'happiness': 2.0,   # 心情值每小时 -2
    'vitality': 1.0,    # 活力值每小时 -1（很久不理会慢慢变淡）
}

# 生病时的加速衰减倍数
SICK_DECAY_MULTIPLIER = 2.0

# 恢复量
RESTORE_AMOUNTS: Dict[str, int] = {
    'feed': 30,    # 喂食恢复饥饿值
    'bath': 40,    # 洗澡恢复清洁度
    'play': 25,    # 玩耍恢复心情值
}

# 活力值增加量（健康互动会让颜色变深）
VITALITY_BOOST: Dict[str, float] = {
    'feed': 3.0,   # 喂食 +3
    'bath': 3.0,   # 洗澡 +3
    'play': 4.0,   # 玩耍 +4
    'click': 0.5,  # 点击 +0.5
}


class SaveManager:
    """存档管理器"""

    def __init__(self):
        self.data: Dict[str, Any] = {}
        self._ensure_save_dir()
        self.load()

    def _ensure_save_dir(self) -> None:
        """确保存档目录存在"""
        SAVE_DIR.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """加载存档，如果不存在则创建新存档"""
        if SAVE_FILE.exists():
            try:
                with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                # 补充旧存档缺少的新字段
                self._migrate_save()
                # 计算离线期间的数值衰减
                self._apply_offline_decay()
            except (json.JSONDecodeError, IOError):
                self._create_new_save()
        else:
            self._create_new_save()
        return self.data

    def _migrate_save(self) -> None:
        """迁移旧存档，补充缺少的字段"""
        for key, default_value in DEFAULT_DATA.items():
            if key not in self.data:
                self.data[key] = default_value

    def _create_new_save(self) -> None:
        """创建新存档"""
        self.data = DEFAULT_DATA.copy()
        self.data['created_at'] = time.time()
        self.data['last_save_time'] = time.time()
        self.save()

    def _apply_offline_decay(self) -> None:
        """计算并应用离线期间的数值衰减"""
        if self.data.get('is_dead'):
            return

        last_save = self.data.get('last_save_time')
        if not last_save:
            return

        now = time.time()
        hours_passed = (now - last_save) / 3600

        if hours_passed <= 0:
            return

        # 检查是否生病（加速衰减）
        is_sick = self._check_if_sick()
        multiplier = SICK_DECAY_MULTIPLIER if is_sick else 1.0

        for stat, rate in DECAY_RATES.items():
            decay = rate * hours_passed * multiplier
            self.data[stat] = max(0, self.data[stat] - decay)

        if hours_passed >= 24:
            self.data['happiness'] = max(15, self.data.get('happiness', 0))

        # 检查是否因为离线太久而死亡
        self._check_death_from_offline(hours_passed)

        # 更新存活天数
        if self.data.get('created_at'):
            days = (now - self.data['created_at']) / 86400
            self.data['alive_days'] = int(days)

        self.data['last_save_time'] = now

    def _check_if_sick(self) -> bool:
        """检查是否处于生病状态（任何数值为0）"""
        return any(self.data.get(stat, 100) <= 0
                   for stat in ['hunger', 'cleanliness', 'happiness'])

    def _check_death_from_offline(self, hours_passed: float) -> None:
        """检查离线期间是否死亡"""
        sick_since = self.data.get('sick_since')

        if self._check_if_sick():
            if sick_since is None:
                self.data['sick_since'] = time.time() - (hours_passed * 3600)
            else:
                sick_duration = (time.time() - sick_since) / 3600
                if sick_duration >= 2:  # 生病超过2小时
                    self.data['is_dead'] = True

    def save(self) -> None:
        """保存当前状态到文件"""
        self.data['last_save_time'] = time.time()
        try:
            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"保存失败: {e}")

    def get_stat(self, stat: str) -> float:
        """获取指定数值"""
        return self.data.get(stat, 0)

    def set_stat(self, stat: str, value: float) -> None:
        """设置指定数值（限制在0-100范围）"""
        self.data[stat] = max(0, min(100, value))
        self._update_sick_status()

    def modify_stat(self, stat: str, delta: float) -> None:
        """修改指定数值"""
        current = self.data.get(stat, 0)
        self.set_stat(stat, current + delta)

    def _update_sick_status(self) -> None:
        """更新生病状态"""
        if self._check_if_sick():
            if self.data.get('sick_since') is None:
                self.data['sick_since'] = time.time()
        else:
            self.data['sick_since'] = None

    def feed(self) -> Tuple[bool, bool]:
        amount = RESTORE_AMOUNTS['feed'] * self.get_mood_multiplier()
        self.modify_stat('hunger', amount)
        self.modify_stat('vitality', VITALITY_BOOST['feed'])
        self.record_interaction()

        full_bonus = False
        if self.data.get('hunger', 0) >= 80:
            self.apply_mood_gain(MOOD_FULL_FEED_BONUS)
            full_bonus = True

        full_service = self.record_service('feed')
        return full_bonus, full_service

    def bath(self) -> Tuple[bool, bool]:
        self.modify_stat('cleanliness', RESTORE_AMOUNTS['bath'])
        self.modify_stat('vitality', VITALITY_BOOST['bath'])
        self.record_interaction()

        clean_bonus = False
        if self.data.get('cleanliness', 0) >= 80:
            self.apply_mood_gain(MOOD_CLEAN_BONUS)
            clean_bonus = True

        full_service = self.record_service('bath')
        return clean_bonus, full_service

    def play(self) -> bool:
        amount = RESTORE_AMOUNTS['play'] * self.get_mood_multiplier()
        self.modify_stat('happiness', amount)
        self.modify_stat('vitality', VITALITY_BOOST['play'])
        self.record_interaction()
        return self.record_service('play')

    def revive(self) -> None:
        """复活（数值重置为50）"""
        self.data['is_dead'] = False
        self.data['sick_since'] = None
        self.data['hunger'] = 50
        self.data['cleanliness'] = 50
        self.data['happiness'] = 50
        self.save()

    def apply_decay(self, seconds: float) -> None:
        """应用时间流逝带来的数值衰减"""
        if self.data.get('is_dead'):
            return

        hours = seconds / 3600
        is_sick = self._check_if_sick()
        multiplier = SICK_DECAY_MULTIPLIER if is_sick else 1.0

        for stat, rate in DECAY_RATES.items():
            decay = rate * hours * multiplier
            self.modify_stat(stat, -decay)

        # 检查生病时长
        self._check_death()

    def _check_death(self) -> None:
        """检查是否应该死亡"""
        sick_since = self.data.get('sick_since')
        if sick_since:
            sick_duration = (time.time() - sick_since) / 3600
            if sick_duration >= 2:
                self.data['is_dead'] = True

    def get_status(self) -> str:
        """获取当前状态"""
        from datetime import datetime

        if self.data.get('is_dead'):
            return 'dead'

        hunger = self.data.get('hunger', 80)
        cleanliness = self.data.get('cleanliness', 80)
        happiness = self.data.get('happiness', 80)

        # 任何数值为0则生病
        if hunger <= 0 or cleanliness <= 0 or happiness <= 0:
            return 'sick'

        # 深夜睡觉（23:00 - 6:00）
        hour = datetime.now().hour
        if hour >= 23 or hour < 6:
            return 'sleep'

        # 摸鱼检测（优先级高于其他状态）
        if self.is_fishing():
            return 'angry'

        # 寂寞检测
        if self.is_lonely():
            return 'lonely'

        # 检查各个数值的状态
        if hunger < 30:
            return 'hungry'
        if cleanliness < 30:
            return 'dirty'
        if happiness < 30:
            return 'sad'

        # 数值都很好则开心
        if hunger > 70 and cleanliness > 70 and happiness > 70:
            return 'happy'

        return 'idle'

    def record_click(self) -> None:
        """记录一次点击"""
        from datetime import datetime
        now = time.time()

        # 记录每日点击
        today = datetime.now().strftime('%Y-%m-%d')
        if 'click_history' not in self.data:
            self.data['click_history'] = {}
        self.data['click_history'][today] = self.data['click_history'].get(today, 0) + 1

        # 记录每小时点击（用于摸鱼检测）
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        if 'hourly_clicks' not in self.data:
            self.data['hourly_clicks'] = {}
        self.data['hourly_clicks'][current_hour] = self.data['hourly_clicks'].get(current_hour, 0) + 1

        self._cleanup_hourly_clicks()
        self.modify_stat('vitality', VITALITY_BOOST['click'])
        mood_bonus = random.randint(MOOD_CLICK_BONUS[0], MOOD_CLICK_BONUS[1])
        self.apply_mood_gain(mood_bonus)

    def record_interaction(self) -> None:
        """记录一次互动（喂食/洗澡/玩耍/点击）"""
        self.data['last_interaction'] = time.time()

    def _cleanup_hourly_clicks(self) -> None:
        """清理超过24小时的点击记录"""
        from datetime import datetime, timedelta
        if 'hourly_clicks' not in self.data:
            return

        cutoff = datetime.now() - timedelta(hours=24)
        cutoff_str = cutoff.strftime('%Y-%m-%d-%H')

        old_keys = [k for k in self.data['hourly_clicks'].keys() if k < cutoff_str]
        for k in old_keys:
            del self.data['hourly_clicks'][k]

    def get_current_hour_clicks(self) -> int:
        """获取当前小时的点击次数"""
        from datetime import datetime
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        if 'hourly_clicks' not in self.data:
            return 0
        return self.data['hourly_clicks'].get(current_hour, 0)

    def is_fishing(self) -> bool:
        return self.get_anger_level() > 0

    def is_work_time(self) -> bool:
        from datetime import datetime
        hour = datetime.now().hour
        weekday = datetime.now().weekday()
        return weekday < 5 and 9 <= hour < 18

    def get_anger_level(self) -> int:
        clicks = self.get_current_hour_clicks()
        if not self.is_work_time():
            return 0
        if clicks > 50:
            return 3
        elif clicks > 35:
            return 2
        elif clicks > 20:
            return 1
        return 0

    def get_hours_since_interaction(self) -> float:
        """获取距离上次互动的小时数"""
        last = self.data.get('last_interaction')
        if not last:
            return 0
        return (time.time() - last) / 3600


    def get_stats_display(self) -> str:
        """获取状态显示文本"""
        vitality = int(self.data.get('vitality', 50))
        if vitality >= 80:
            vitality_desc = "活力满满！"
        elif vitality >= 60:
            vitality_desc = "精神不错"
        elif vitality >= 40:
            vitality_desc = "一般般"
        elif vitality >= 20:
            vitality_desc = "有点蔫…"
        else:
            vitality_desc = "快褪色了…"

        # 摸鱼状态
        hourly_clicks = self.get_current_hour_clicks()
        if hourly_clicks > FISHING_THRESHOLD:
            fishing_status = f"🐟 摸鱼中！({hourly_clicks}次/小时)"
        elif hourly_clicks > FISHING_THRESHOLD // 2:
            fishing_status = f"⚠️ 快摸鱼了 ({hourly_clicks}次/小时)"
        else:
            fishing_status = f"✅ 正常 ({hourly_clicks}次/小时)"

        hours_since = self.get_hours_since_interaction()
        lonely_threshold = self.get_loneliness_threshold()
        if hours_since >= lonely_threshold:
            lonely_status = f"😢 寂寞了 ({hours_since:.1f}小时没互动)"
        elif hours_since >= 1:
            lonely_status = f"🙂 还好 ({hours_since:.1f}小时前互动)"
        else:
            lonely_status = "😊 刚刚互动过"

        trust = int(self.get_trust())
        trust_desc = self.get_trust_description()
        streak = self.data.get('trust_streak', 0)

        return (
            f"饥饿值: {int(self.data.get('hunger', 0))}/100\n"
            f"清洁度: {int(self.data.get('cleanliness', 0))}/100\n"
            f"心情值: {int(self.data.get('happiness', 0))}/100\n"
            f"活力值: {vitality}/100 ({vitality_desc})\n"
            f"───────────\n"
            f"信任度: {trust}/100 ({trust_desc})\n"
            f"连续照顾: {streak}天\n"
            f"───────────\n"
            f"点击频率: {fishing_status}\n"
            f"互动状态: {lonely_status}\n"
            f"───────────\n"
            f"存活天数: {self.data.get('alive_days', 0)}天"
        )

    def get_vitality(self) -> float:
        return self.data.get('vitality', 50)

    def update_body_type(self) -> None:
        history = self.data.get('hunger_history', [])
        hunger = self.data.get('hunger', 80)
        history.append(hunger)
        if len(history) > 168:
            history = history[-168:]
        self.data['hunger_history'] = history

        old_type = self.data.get('body_type', 'normal')
        new_type = old_type

        if len(history) >= 48:
            avg = sum(history) / len(history)
            if avg >= 90:
                new_type = 'fat'
            elif avg <= 40:
                new_type = 'thin'
            else:
                new_type = 'normal'

        if new_type != old_type:
            self.data['body_type'] = new_type

    def get_body_type(self) -> str:
        return self.data.get('body_type', 'normal')

    # ========== 信任度系统 ==========

    def get_trust(self) -> float:
        return self.data.get('trust', 50)

    def get_trust_bonus(self) -> float:
        return self.get_trust() / 100.0

    def modify_trust(self, delta: float) -> None:
        current = self.data.get('trust', 50)
        self.data['trust'] = max(0, min(100, current + delta))

    def get_trust_description(self) -> str:
        trust = self.get_trust()
        if trust >= 81:
            return "绝对信任！"
        elif trust >= 61:
            return "最喜欢你了！"
        elif trust >= 41:
            return "你还不错嘛"
        elif trust >= 21:
            return "有点信任你了"
        else:
            return "警惕中..."

    def get_loneliness_threshold(self) -> float:
        return LONELY_HOURS_BASE + self.get_trust_bonus() * 2

    def is_lonely(self) -> bool:
        return self.get_hours_since_interaction() >= self.get_loneliness_threshold()

    def check_daily_settlement(self) -> None:
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        last_check = self.data.get('last_trust_check_date')

        if last_check == today:
            return

        hour = datetime.now().hour
        if hour < 6:
            return

        if last_check:
            self._do_daily_settlement()

        self.data['last_trust_check_date'] = today
        mh = self.data.get('mood_history', {})
        mh['morning_greeted_today'] = False
        mh['services_this_hour'] = []
        self.data['mood_history'] = mh

        sd = self.data.get('sleep_data', {})
        sd['disturb_count_tonight'] = 0
        self.data['sleep_data'] = sd

    def _do_daily_settlement(self) -> None:
        hunger = self.data.get('hunger', 0)
        clean = self.data.get('cleanliness', 0)
        happy = self.data.get('happiness', 0)

        if hunger >= 50 and clean >= 50 and happy >= 50:
            streak = self.data.get('trust_streak', 0) + 1
            self.data['trust_streak'] = streak
            if streak >= 7:
                self.modify_trust(TRUST_STREAK_7_BONUS)
            elif streak >= 3:
                self.modify_trust(TRUST_STREAK_3_BONUS)
            else:
                self.modify_trust(TRUST_DAILY_GOOD)
        else:
            if hunger <= 0 or clean <= 0 or happy <= 0:
                self.modify_trust(TRUST_ZERO_PENALTY)
            if hunger < 30 and clean < 30 and happy < 30:
                self.modify_trust(TRUST_NEGLECT_PENALTY)
            self.data['trust_streak'] = 0

    def on_death(self) -> None:
        self.modify_trust(TRUST_DEATH_PENALTY)

    # ========== 心情系统 ==========

    def get_mood_multiplier(self) -> float:
        happiness = self.data.get('happiness', 50)
        if happiness < 10:
            return 1.0
        elif happiness < 25:
            return 0.5
        return 1.0

    def apply_mood_gain(self, base_amount: float) -> float:
        trust_bonus = self.get_trust_bonus()
        multiplier = self.get_mood_multiplier()
        final = base_amount * (1 + trust_bonus * 0.4) * multiplier
        self.modify_stat('happiness', final)
        return final

    def apply_mood_decay(self, base_rate: float, hours: float) -> float:
        trust_bonus = self.get_trust_bonus()
        decay_multiplier = 1 - trust_bonus * 0.25
        happiness = self.data.get('happiness', 50)
        hunger = self.data.get('hunger', 50)
        clean = self.data.get('cleanliness', 50)

        extra = 0
        if self.is_lonely():
            extra += 2
        if hunger < 20:
            extra += 1
        if clean < 20:
            extra += 1

        sd = self.data.get('sleep_data', {})
        if sd.get('had_bad_sleep'):
            from datetime import datetime
            if datetime.now().hour < 8:
                extra += 2

        final_rate = (base_rate + extra) * decay_multiplier
        decay = final_rate * hours
        self.modify_stat('happiness', -decay)
        return decay

    def check_morning_greeting(self) -> bool:
        from datetime import datetime
        hour = datetime.now().hour
        if not (6 <= hour < 9):
            return False

        mh = self.data.get('mood_history', {})
        if mh.get('morning_greeted_today'):
            return False

        mh['morning_greeted_today'] = True
        self.data['mood_history'] = mh
        self.apply_mood_gain(MOOD_MORNING_BONUS)
        return True

    def record_service(self, service_type: str) -> bool:
        from datetime import datetime
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')

        mh = self.data.get('mood_history', {})
        last_hour = mh.get('last_full_service_hour')
        services = mh.get('services_this_hour', [])

        if last_hour != current_hour:
            services = []
            mh['last_full_service_hour'] = current_hour

        if service_type not in services:
            services.append(service_type)

        mh['services_this_hour'] = services
        self.data['mood_history'] = mh

        if set(services) >= {'feed', 'bath', 'play'}:
            mh['services_this_hour'] = []
            self.data['mood_history'] = mh
            self.apply_mood_gain(MOOD_FULL_SERVICE_BONUS)
            return True
        return False

    def can_comfort(self) -> bool:
        mh = self.data.get('mood_history', {})
        last_used = mh.get('comfort_last_used')
        if not last_used:
            return True
        return time.time() - last_used >= COMFORT_COOLDOWN

    def get_comfort_cooldown_remaining(self) -> int:
        mh = self.data.get('mood_history', {})
        last_used = mh.get('comfort_last_used')
        if not last_used:
            return 0
        remaining = COMFORT_COOLDOWN - (time.time() - last_used)
        return max(0, int(remaining))

    def comfort(self) -> bool:
        if not self.can_comfort():
            return False
        mh = self.data.get('mood_history', {})
        mh['comfort_last_used'] = time.time()
        self.data['mood_history'] = mh
        self.modify_stat('happiness', MOOD_COMFORT_AMOUNT)
        self.modify_stat('vitality', 5)
        self.record_interaction()
        return True

    # ========== 睡眠打扰系统 ==========

    def is_sleep_time(self) -> bool:
        from datetime import datetime
        hour = datetime.now().hour
        return hour >= 23 or hour < 6

    def record_sleep_disturb(self) -> int:
        sd = self.data.get('sleep_data', {})
        count = sd.get('disturb_count_tonight', 0) + 1
        sd['disturb_count_tonight'] = count

        if count >= 3:
            sd['had_bad_sleep'] = True

        self.data['sleep_data'] = sd

        if count == 1:
            self.modify_stat('happiness', MOOD_NIGHT_DISTURB_FIRST)
        else:
            self.modify_stat('happiness', MOOD_NIGHT_DISTURB_AFTER)

        return count

    def get_sleep_disturb_count(self) -> int:
        sd = self.data.get('sleep_data', {})
        return sd.get('disturb_count_tonight', 0)

    def record_pre_sleep_mood(self) -> None:
        from datetime import datetime
        hour = datetime.now().hour
        if hour == 22:
            sd = self.data.get('sleep_data', {})
            sd['pre_sleep_mood'] = self.data.get('happiness', 50)
            self.data['sleep_data'] = sd

    def get_pre_sleep_mood(self) -> float:
        sd = self.data.get('sleep_data', {})
        return sd.get('pre_sleep_mood', 50)

    def clear_bad_sleep(self) -> None:
        sd = self.data.get('sleep_data', {})
        sd['had_bad_sleep'] = False
        self.data['sleep_data'] = sd

    # ========== 每日状态管理（跨天检测） ==========

    def get_daily_state(self) -> Dict:
        """获取每日状态"""
        ds = self.data.get('daily_state', {})
        # 确保所有字段存在
        defaults = {
            'last_active_date': None,
            'greeted_today': False,
            'papers_fetched_today': False,
            'dream_settled_today': False,
            'last_dream': None,
            'comforted_after_nightmare': False,
        }
        for key, default in defaults.items():
            if key not in ds:
                ds[key] = default
        self.data['daily_state'] = ds
        return ds

    def check_day_change(self) -> bool:
        """检查是否跨天了，返回 True 表示是新的一天"""
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        ds = self.get_daily_state()
        last_active = ds.get('last_active_date')

        if last_active != today:
            # 新的一天！重置每日状态
            ds['last_active_date'] = today
            ds['greeted_today'] = False
            ds['papers_fetched_today'] = False
            ds['dream_settled_today'] = False
            ds['comforted_after_nightmare'] = False
            self.data['daily_state'] = ds
            self.save()
            return True
        return False

    def is_papers_fetched_today(self) -> bool:
        """今天是否已抓取论文"""
        ds = self.get_daily_state()
        return ds.get('papers_fetched_today', False)

    def mark_papers_fetched(self) -> None:
        """标记今天已抓取论文"""
        ds = self.get_daily_state()
        ds['papers_fetched_today'] = True
        self.data['daily_state'] = ds

    def is_greeted_today(self) -> bool:
        """今天是否已打过招呼"""
        ds = self.get_daily_state()
        return ds.get('greeted_today', False)

    def mark_greeted(self) -> None:
        """标记今天已打招呼"""
        ds = self.get_daily_state()
        ds['greeted_today'] = True
        self.data['daily_state'] = ds

    def settle_dream(self) -> Optional[str]:
        """结算梦境，返回梦境类型 ('good', 'nightmare', 'none')"""
        ds = self.get_daily_state()

        # 今天已结算过，返回上次结果
        if ds.get('dream_settled_today'):
            return ds.get('last_dream')

        # 首次运行没有历史记录，跳过梦境结算
        if ds.get('last_active_date') is None:
            return None

        # 生成梦境
        dream = self._generate_dream()

        # 应用心情影响
        if dream == 'good':
            self.modify_stat('happiness', 10)
        elif dream == 'nightmare':
            self.modify_stat('happiness', -8)

        # 记录
        ds['last_dream'] = dream
        ds['dream_settled_today'] = True
        self.data['daily_state'] = ds
        self.save()

        return dream

    def _generate_dream(self) -> str:
        """根据睡前心情生成梦境"""
        sd = self.data.get('sleep_data', {})
        pre_sleep_mood = sd.get('pre_sleep_mood', 50)

        # 根据心情调整概率
        if pre_sleep_mood >= 70:
            weights = [0.50, 0.40, 0.10]  # 美梦概率高
        elif pre_sleep_mood <= 30:
            weights = [0.15, 0.50, 0.35]  # 噩梦概率高
        else:
            weights = [0.30, 0.50, 0.20]  # 正常概率

        dreams = ['good', 'none', 'nightmare']
        return random.choices(dreams, weights=weights)[0]

    def get_last_dream(self) -> Optional[str]:
        """获取最近一次梦境"""
        ds = self.get_daily_state()
        return ds.get('last_dream')

    def comfort_after_nightmare(self) -> bool:
        """噩梦后安慰，返回是否成功"""
        ds = self.get_daily_state()
        if ds.get('last_dream') != 'nightmare':
            return False
        if ds.get('comforted_after_nightmare'):
            return False

        self.modify_stat('happiness', 5)
        ds['comforted_after_nightmare'] = True
        self.data['daily_state'] = ds
        return True

    # ========== 情绪系统（生气维度） ==========

    def get_emotion_data(self) -> Dict:
        """获取情绪数据"""
        em = self.data.get('emotion', {})
        # 确保所有字段存在
        defaults = {
            'anger_level': 0,
            'anger_cooldown': 0,
            'anger_click_count': 0,
            'anger_click_window_start': None,
            'anger_shake_count': 0,
            'anger_last_shake_time': None,
            'night_disturb_count': 0,
            'night_disturb_date': None,
            'cold_war_feed_count': 0,
            'emotion_state': 'normal',
        }
        for key, default in defaults.items():
            if key not in em:
                em[key] = default
        self.data['emotion'] = em
        return em

    def get_emotion_state(self) -> str:
        """获取当前情绪状态"""
        self._update_emotion_state()
        em = self.get_emotion_data()
        return em.get('emotion_state', 'normal')

    def get_new_anger_level(self) -> int:
        """获取新的生气等级（基于情绪系统）"""
        em = self.get_emotion_data()
        return em.get('anger_level', 0)

    def _update_emotion_state(self) -> None:
        """根据生气程度和心情值判定当前情绪状态"""
        em = self.get_emotion_data()
        anger = em.get('anger_level', 0)
        happiness = self.data.get('happiness', 50)

        # 生气优先级最高（因为这是针对用户的即时反应）
        if anger >= 3:
            em['emotion_state'] = 'super_annoyed'
        elif anger >= 2:
            em['emotion_state'] = 'angry'
        elif anger >= 1:
            em['emotion_state'] = 'annoyed'
        # 然后看心情
        elif happiness <= 15:
            em['emotion_state'] = 'very_sad'
        elif happiness <= 30:
            em['emotion_state'] = 'sad'
        elif happiness >= 70 and self._all_needs_satisfied():
            em['emotion_state'] = 'happy'
        else:
            em['emotion_state'] = 'normal'

        self.data['emotion'] = em

    def _all_needs_satisfied(self) -> bool:
        """检查所有需求是否满足"""
        hunger = self.data.get('hunger', 0)
        clean = self.data.get('cleanliness', 0)
        return hunger > 70 and clean > 70

    def add_anger_click(self) -> Optional[int]:
        """增加生气点击计数，返回触发的生气等级（如果触发了的话）"""
        # 只在工作时间触发
        if not self.is_work_time():
            return None

        em = self.get_emotion_data()
        now = time.time()
        window_start = em.get('anger_click_window_start')

        # 如果窗口不存在或超过 10 分钟，重置
        if window_start is None or (now - window_start) > ANGER_CLICK_WINDOW:
            em['anger_click_count'] = 1
            em['anger_click_window_start'] = now
        else:
            em['anger_click_count'] += 1

        self.data['emotion'] = em
        clicks = em['anger_click_count']

        # 检查是否触发生气
        triggered_level = None
        if clicks >= ANGER_CLICK_THRESHOLDS[3]:
            triggered_level = 3
        elif clicks >= ANGER_CLICK_THRESHOLDS[2]:
            triggered_level = 2
        elif clicks >= ANGER_CLICK_THRESHOLDS[1]:
            triggered_level = 1

        # 如果触发了更高等级的生气
        current_level = em.get('anger_level', 0)
        if triggered_level and triggered_level > current_level:
            self._trigger_anger(triggered_level)
            return triggered_level

        return None

    def add_anger_shake(self) -> Optional[int]:
        """增加摇晃计数，返回触发的生气等级"""
        em = self.get_emotion_data()
        now = time.time()
        last_shake = em.get('anger_last_shake_time')

        # 超过 30 秒没摇晃，重置计数
        if last_shake is None or (now - last_shake) > ANGER_SHAKE_RESET_TIME:
            em['anger_shake_count'] = 1
        else:
            em['anger_shake_count'] += 1

        em['anger_last_shake_time'] = now
        self.data['emotion'] = em

        shakes = em['anger_shake_count']
        current_level = em.get('anger_level', 0)

        # 检查是否触发生气
        if shakes >= ANGER_SHAKE_THRESHOLDS[3] and current_level < 3:
            self._trigger_anger(3)
            return 3
        elif shakes >= ANGER_SHAKE_THRESHOLDS[2] and current_level < 2:
            self._trigger_anger(2)
            return 2

        return None

    def handle_night_disturb(self) -> Optional[int]:
        """处理深夜打扰，返回触发的生气等级"""
        from datetime import datetime
        now = datetime.now()
        hour = now.hour
        today = now.strftime('%Y-%m-%d')

        # 检查是否是深夜
        if not (hour >= 23 or hour < 6):
            return None

        em = self.get_emotion_data()

        # 检查是否是新的一晚（重置计数）
        if em.get('night_disturb_date') != today:
            em['night_disturb_date'] = today
            em['night_disturb_count'] = 0

        em['night_disturb_count'] += 1
        count = em['night_disturb_count']
        self.data['emotion'] = em

        # 根据打扰次数决定生气等级
        if count == 1:
            self._trigger_anger(1)
            self.modify_stat('happiness', -3)
            return 1
        elif count == 2:
            self._trigger_anger(2)
            self.modify_stat('happiness', -5)
            return 2
        else:  # 3+ 次
            self._trigger_anger(3)
            self.modify_stat('happiness', -10)
            return 3

    def _trigger_anger(self, level: int) -> None:
        """触发生气状态"""
        em = self.get_emotion_data()
        current_level = em.get('anger_level', 0)

        # 只能升级，不能降级
        if level <= current_level:
            return

        em['anger_level'] = level

        # 设置冷战时间
        if level >= 2:
            em['anger_cooldown'] = COLD_WAR_DURATION.get(level, 30)
            em['cold_war_feed_count'] = 0

        # 重置计数
        self._reset_anger_counts()

        # 扣除心情
        penalty = ANGER_HAPPINESS_PENALTY.get(level, 0)
        self.modify_stat('happiness', penalty)

        self.data['emotion'] = em
        self._update_emotion_state()

    def _reset_anger_counts(self) -> None:
        """重置生气计数"""
        em = self.get_emotion_data()
        em['anger_click_count'] = 0
        em['anger_click_window_start'] = None
        em['anger_shake_count'] = 0
        em['anger_last_shake_time'] = None
        self.data['emotion'] = em

    def cold_war_tick(self) -> bool:
        """冷战倒计时（每秒调用），返回是否自动消气了"""
        em = self.get_emotion_data()

        if em.get('anger_cooldown', 0) <= 0:
            return False

        em['anger_cooldown'] -= 1
        self.data['emotion'] = em

        # 冷战期间每 60 秒心情 -2
        if em['anger_cooldown'] % 60 == 0 and em['anger_cooldown'] > 0:
            self.modify_stat('happiness', -2)

        # 超级不爽不会自动解除，必须道歉
        if em['anger_cooldown'] <= 0 and em.get('anger_level', 0) < 3:
            self._calm_down()
            return True

        return False

    def _calm_down(self) -> None:
        """消气"""
        em = self.get_emotion_data()
        em['anger_level'] = 0
        em['anger_cooldown'] = 0
        em['cold_war_feed_count'] = 0
        self._reset_anger_counts()
        self.modify_stat('happiness', CALM_DOWN_HAPPINESS_BONUS)
        self.data['emotion'] = em
        self._update_emotion_state()

    def feed_during_cold_war(self) -> Tuple[bool, str]:
        """冷战期间喂食，返回 (是否成功, 消息类型)"""
        em = self.get_emotion_data()
        level = em.get('anger_level', 0)

        if level == 0:
            return False, ''

        if level == 2:
            # 普通生气：喂食减少 10 秒冷战时间
            em['anger_cooldown'] = max(0, em.get('anger_cooldown', 0) - 10)
            self.data['emotion'] = em
            if em['anger_cooldown'] <= 0:
                self._calm_down()
                return True, 'calm_down'
            return True, 'reduce_cooldown'
        elif level == 3:
            # 超级不爽：喂食不能直接解除，但可以让小铁皮态度软化一点
            em['cold_war_feed_count'] = em.get('cold_war_feed_count', 0) + 1
            self.data['emotion'] = em
            if em['cold_war_feed_count'] >= 3:
                return True, 'softened'
            return True, 'still_angry'

        return False, ''

    def check_apology(self, user_input: str) -> bool:
        """检查用户是否道歉"""
        apology_words = ['对不起', '抱歉', '我错了', 'sorry', '对不起啦', '原谅我', '不好意思']

        em = self.get_emotion_data()
        if em.get('anger_level', 0) < 3:
            return False

        for word in apology_words:
            if word in user_input.lower():
                self._accept_apology()
                return True

        return False

    def _accept_apology(self) -> None:
        """接受道歉"""
        em = self.get_emotion_data()
        em['anger_level'] = 0
        em['anger_cooldown'] = 0
        em['cold_war_feed_count'] = 0
        self._reset_anger_counts()
        self.modify_stat('happiness', APOLOGY_HAPPINESS_BONUS)
        self.data['emotion'] = em
        self._update_emotion_state()

    def is_in_cold_war(self) -> bool:
        """是否在冷战中"""
        em = self.get_emotion_data()
        return em.get('anger_level', 0) >= 2

    def get_cold_war_remaining(self) -> int:
        """获取冷战剩余时间（秒）"""
        em = self.get_emotion_data()
        return em.get('anger_cooldown', 0)

    def should_show_apology_dialog(self) -> bool:
        """是否应该显示道歉对话框"""
        em = self.get_emotion_data()
        return em.get('anger_level', 0) >= 3
