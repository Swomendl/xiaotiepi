"""
items.py - 小铁皮道具系统
包含道具定义、精灵图和解锁条件
"""

from typing import Dict, List, Optional, Tuple, Any


# ═══════════════════════════════════════════════════════════════
#  道具槽位和稀有度
# ═══════════════════════════════════════════════════════════════

class ItemSlot:
    HEAD = 'head'
    FACE = 'face'
    NECK = 'neck'
    HAND = 'hand'
    EFFECT = 'effect'


class ItemRarity:
    COMMON = 'common'
    UNCOMMON = 'uncommon'
    RARE = 'rare'
    EPIC = 'epic'
    LEGENDARY = 'legendary'


RARITY_COLORS = {
    'common': '#FFFFFF',
    'uncommon': '#4ADE80',
    'rare': '#60A5FA',
    'epic': '#A855F7',
    'legendary': '#F59E0B',
}

RARITY_NAMES = {
    'common': '普通',
    'uncommon': '优秀',
    'rare': '稀有',
    'epic': '史诗',
    'legendary': '传说',
}


# ═══════════════════════════════════════════════════════════════
#  道具颜色
# ═══════════════════════════════════════════════════════════════

ITEM_COLORS = {
    # 冒险帽（绿色系）
    40: '#4A7C4E',  # 森林绿 - 帽身
    41: '#6B9E6F',  # 浅绿 - 帽子高光
    42: '#3D5940',  # 深绿 - 帽子阴影

    # 蝴蝶结（粉色系）
    43: '#FF69B4',  # 粉色 - 主色
    44: '#FF8DC7',  # 浅粉 - 高光
    45: '#DB4B8A',  # 深粉 - 阴影

    # 睡帽（蓝色系）
    46: '#4169E1',  # 皇家蓝 - 主色
    47: '#87CEEB',  # 天蓝 - 条纹
    48: '#2D4A8B',  # 深蓝 - 阴影

    # 眼镜
    49: '#2D2D2D',  # 黑色框
    50: '#4A4A4A',  # 灰色框

    # 围巾（红色系）
    51: '#DC2626',  # 红色 - 主色
    52: '#EF4444',  # 浅红 - 高光
    53: '#B91C1C',  # 深红 - 阴影

    # 皇冠（金色系）
    54: '#F59E0B',  # 金色 - 主色
    55: '#FCD34D',  # 浅金 - 高光
    56: '#D97706',  # 深金 - 阴影
    57: '#EF4444',  # 红宝石
    58: '#3B82F6',  # 蓝宝石
}


# ═══════════════════════════════════════════════════════════════
#  道具精灵图
# ═══════════════════════════════════════════════════════════════

# 冒险小帽 (8x4)
SPRITE_HAT_ADVENTURE = [
    [0,  0, 40, 40, 40, 40,  0,  0],
    [0, 40, 41, 41, 41, 40, 40,  0],
    [40, 40, 40, 40, 40, 40, 40, 40],
    [0, 42,  0,  0,  0,  0, 42,  0],
]

# 蝴蝶结 (7x4)
SPRITE_HAT_BOW = [
    [43,  0,  0,  0,  0,  0, 43],
    [43, 43, 44, 45, 44, 43, 43],
    [0,  43, 45, 45, 45, 43,  0],
    [0,   0, 45, 45, 45,  0,  0],
]

# 睡帽 (8x5)
SPRITE_HAT_SLEEP = [
    [0,  0,  0,  0,  0, 14, 14,  0],
    [0,  0,  0, 46, 47, 46, 14,  0],
    [0,  0, 46, 47, 46, 47, 46,  0],
    [0, 46, 47, 46, 47, 46, 47, 46],
    [48, 46, 46, 46, 46, 46, 46, 48],
]

# 小皇冠 (8x4)
SPRITE_HAT_CROWN = [
    [0, 55,  0, 55,  0, 55,  0,  0],
    [54, 54, 54, 54, 54, 54, 54,  0],
    [54, 57, 54, 58, 54, 57, 54,  0],
    [56, 54, 54, 54, 54, 54, 56,  0],
]

# 小花 (5x4)
SPRITE_HAT_FLOWER = [
    [0, 44,  0, 44,  0],
    [44, 43, 44, 43, 44],
    [0, 44, 55, 44,  0],
    [0,  0, 41,  0,  0],
]

# 圆框眼镜 (8x3)
SPRITE_GLASSES_ROUND = [
    [0, 49, 49,  0,  0, 49, 49,  0],
    [49,  0,  0, 49, 49,  0,  0, 49],
    [0, 49, 49,  0,  0, 49, 49,  0],
]

# 学者眼镜 (8x2)
SPRITE_GLASSES_SCHOLAR = [
    [49, 49, 49, 49, 49, 49, 49, 49],
    [49,  0, 49, 49, 49,  0, 49,  0],
]

# 红围巾 (10x3)
SPRITE_SCARF_RED = [
    [0, 51, 51, 51, 51, 51, 51, 51, 51,  0],
    [51, 52, 51, 51, 51, 51, 51, 51, 52, 51],
    [53,  0,  0,  0,  0,  0,  0,  0,  0, 53],
]

# 彩虹围巾 (10x3)
SPRITE_SCARF_RAINBOW = [
    [0, 51, 54, 55, 41, 47, 44, 54, 51,  0],
    [51, 52, 55, 41, 47, 44, 55, 41, 52, 51],
    [53,  0,  0,  0,  0,  0,  0,  0,  0, 53],
]


# ═══════════════════════════════════════════════════════════════
#  特效配置
# ═══════════════════════════════════════════════════════════════

EFFECT_SPARKLE_CONFIG = {
    'type': 'particle',
    'particle_sprite': [[55], [14]],
    'count': 5,
    'radius': 20,
    'speed': 0.5,
    'fade': True,
}

EFFECT_HEARTS_CONFIG = {
    'type': 'particle',
    'particle_sprite': [
        [0, 43, 0, 43, 0],
        [43, 43, 43, 43, 43],
        [0, 43, 43, 43, 0],
        [0, 0, 43, 0, 0],
    ],
    'count': 3,
    'radius': 25,
    'speed': 0.3,
    'orbit': True,
}


# ═══════════════════════════════════════════════════════════════
#  道具定义
# ═══════════════════════════════════════════════════════════════

ITEMS: Dict[str, Dict[str, Any]] = {
    # ═══════════════════════════════════════
    # 头部道具
    # ═══════════════════════════════════════
    'hat_adventure': {
        'id': 'hat_adventure',
        'name': '冒险小帽',
        'slot': ItemSlot.HEAD,
        'description': '一顶充满冒险精神的小帽子',
        'rarity': ItemRarity.COMMON,
        'sprite': SPRITE_HAT_ADVENTURE,
        'offset': (1, -3),
        'unlock': {'type': 'default'},
    },
    'hat_bow': {
        'id': 'hat_bow',
        'name': '蝴蝶结',
        'slot': ItemSlot.HEAD,
        'description': '可爱的粉色蝴蝶结',
        'rarity': ItemRarity.COMMON,
        'sprite': SPRITE_HAT_BOW,
        'offset': (2, -2),
        'unlock': {'type': 'default'},
    },
    'hat_sleep': {
        'id': 'hat_sleep',
        'name': '睡帽',
        'slot': ItemSlot.HEAD,
        'description': '蓝色条纹的经典睡帽',
        'rarity': ItemRarity.COMMON,
        'sprite': SPRITE_HAT_SLEEP,
        'offset': (1, -4),
        'unlock': {'type': 'default'},
    },
    'hat_crown': {
        'id': 'hat_crown',
        'name': '小皇冠',
        'slot': ItemSlot.HEAD,
        'description': '闪闪发光的金色皇冠，传说中的道具',
        'rarity': ItemRarity.LEGENDARY,
        'sprite': SPRITE_HAT_CROWN,
        'offset': (1, -3),
        'unlock': {'type': 'level', 'level': 50},
    },
    'hat_flower': {
        'id': 'hat_flower',
        'name': '小花',
        'slot': ItemSlot.HEAD,
        'description': '戴在耳边的粉色小花',
        'rarity': ItemRarity.UNCOMMON,
        'sprite': SPRITE_HAT_FLOWER,
        'offset': (6, -1),
        'unlock': {'type': 'level', 'level': 10},
    },

    # ═══════════════════════════════════════
    # 脸部道具
    # ═══════════════════════════════════════
    'glasses_round': {
        'id': 'glasses_round',
        'name': '圆框眼镜',
        'slot': ItemSlot.FACE,
        'description': '文艺复古的圆框眼镜',
        'rarity': ItemRarity.COMMON,
        'sprite': SPRITE_GLASSES_ROUND,
        'offset': (1, 3),
        'unlock': {'type': 'default'},
    },
    'glasses_scholar': {
        'id': 'glasses_scholar',
        'name': '学者眼镜',
        'slot': ItemSlot.FACE,
        'description': '方框眼镜，读了太多论文的证明',
        'rarity': ItemRarity.RARE,
        'sprite': SPRITE_GLASSES_SCHOLAR,
        'offset': (1, 4),
        'unlock': {'type': 'stat', 'stat': 'paper_reads', 'value': 50},
    },

    # ═══════════════════════════════════════
    # 脖子道具
    # ═══════════════════════════════════════
    'scarf_red': {
        'id': 'scarf_red',
        'name': '红围巾',
        'slot': ItemSlot.NECK,
        'description': '温暖的红色小围巾',
        'rarity': ItemRarity.COMMON,
        'sprite': SPRITE_SCARF_RED,
        'offset': (0, 6),
        'unlock': {'type': 'default'},
    },
    'scarf_rainbow': {
        'id': 'scarf_rainbow',
        'name': '彩虹围巾',
        'slot': ItemSlot.NECK,
        'description': '七彩的围巾，坚持照顾30天的证明',
        'rarity': ItemRarity.EPIC,
        'sprite': SPRITE_SCARF_RAINBOW,
        'offset': (0, 6),
        'unlock': {'type': 'stat', 'stat': 'consecutive_care_max', 'value': 30},
    },

    # ═══════════════════════════════════════
    # 特效道具
    # ═══════════════════════════════════════
    'effect_sparkle': {
        'id': 'effect_sparkle',
        'name': '闪闪发光',
        'slot': ItemSlot.EFFECT,
        'description': '浑身散发着光芒（洗了100次澡的结果）',
        'rarity': ItemRarity.RARE,
        'sprite': None,
        'config': EFFECT_SPARKLE_CONFIG,
        'offset': (0, 0),
        'unlock': {'type': 'stat', 'stat': 'clean_count', 'value': 100},
    },
    'effect_hearts': {
        'id': 'effect_hearts',
        'name': '爱心环绕',
        'slot': ItemSlot.EFFECT,
        'description': '被爱包围着',
        'rarity': ItemRarity.EPIC,
        'sprite': None,
        'config': EFFECT_HEARTS_CONFIG,
        'offset': (0, 0),
        'unlock': {'type': 'trust', 'value': 100},
    },
}


# ═══════════════════════════════════════════════════════════════
#  状态适配规则
# ═══════════════════════════════════════════════════════════════

# 这些状态下隐藏所有道具
HIDE_ITEMS_STATES = ['sleep', 'dizzy', 'dead', 'sick']

# 拖拽状态的偏移调整
DRAGGING_OFFSET_ADJUST = {
    'head': (0, 1),
    'face': (0, 1),
    'neck': (0, 0),
}

# 体型偏移补偿
BODY_TYPE_OFFSET = {
    'normal': (0, 0),
    'fat': (1, 0),
    'thin': (-1, 0),
}


# ═══════════════════════════════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════════════════════════════

def should_show_items(state: str) -> bool:
    """判断当前状态是否显示道具"""
    return state not in HIDE_ITEMS_STATES


def get_item_offset(item: Dict, state: str, body_type: str) -> Tuple[int, int]:
    """获取道具的最终偏移量"""
    base_offset = item.get('offset', (0, 0))

    # 体型补偿
    body_adj = BODY_TYPE_OFFSET.get(body_type, (0, 0))

    # 拖拽调整
    drag_adj = (0, 0)
    if state == 'dragging':
        slot = item.get('slot', '')
        drag_adj = DRAGGING_OFFSET_ADJUST.get(slot, (0, 0))

    return (
        base_offset[0] + body_adj[0] + drag_adj[0],
        base_offset[1] + body_adj[1] + drag_adj[1]
    )


def get_item(item_id: str) -> Optional[Dict]:
    """获取道具数据"""
    return ITEMS.get(item_id)


def get_item_name(item_id: str) -> str:
    """获取道具名称"""
    item = ITEMS.get(item_id)
    return item['name'] if item else item_id


def get_items_by_slot(slot: str) -> List[Dict]:
    """获取指定槽位的所有道具"""
    return [item for item in ITEMS.values() if item.get('slot') == slot]


def check_unlock_condition(unlock: Dict, save_manager) -> bool:
    """检查道具是否满足解锁条件"""
    unlock_type = unlock.get('type', 'default')

    if unlock_type == 'default':
        return True

    if unlock_type == 'level':
        required_level = unlock.get('level', 1)
        current_level = save_manager.get_level()
        return current_level >= required_level

    if unlock_type == 'stat':
        stat_name = unlock.get('stat', '')
        required_value = unlock.get('value', 0)
        stats = save_manager.get_behavior_stats()
        current_value = stats.get(stat_name, 0)
        return current_value >= required_value

    if unlock_type == 'trust':
        required_trust = unlock.get('value', 0)
        current_trust = save_manager.get_trust()
        return current_trust >= required_trust

    return False


def check_all_unlocks(save_manager) -> List[str]:
    """检查所有未解锁道具，返回新解锁的道具ID列表"""
    inventory = save_manager.get_inventory()
    owned = set(inventory.get('owned_items', []))
    new_unlocks = []

    for item_id, item in ITEMS.items():
        if item_id in owned:
            continue

        unlock = item.get('unlock', {'type': 'default'})
        if check_unlock_condition(unlock, save_manager):
            if save_manager.unlock_item(item_id):
                new_unlocks.append(item_id)

    return new_unlocks


def get_unlock_description(item_id: str) -> str:
    """获取道具解锁条件描述"""
    item = ITEMS.get(item_id)
    if not item:
        return "未知道具"

    unlock = item.get('unlock', {'type': 'default'})
    unlock_type = unlock.get('type', 'default')

    if unlock_type == 'default':
        return "默认拥有"
    elif unlock_type == 'level':
        return f"达到 Lv.{unlock.get('level', 1)}"
    elif unlock_type == 'stat':
        stat_names = {
            'paper_reads': '论文阅读',
            'clean_count': '洗澡次数',
            'feed_count': '喂食次数',
            'play_count': '玩耍次数',
            'consecutive_care_max': '最长连续照顾',
        }
        stat = unlock.get('stat', '')
        stat_name = stat_names.get(stat, stat)
        return f"{stat_name} 达到 {unlock.get('value', 0)}"
    elif unlock_type == 'trust':
        return f"亲密度达到 {unlock.get('value', 0)}"

    return "未知条件"
