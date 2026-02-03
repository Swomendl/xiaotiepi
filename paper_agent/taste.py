import json
from datetime import datetime
from typing import List, Dict

from .config import (
    TASTE_PROFILE_FILE, TASTE_DECAY_RATE, EVOLVED_KEYWORD_THRESHOLD,
    SEED_KEYWORDS, SAVE_DIR
)


class TasteProfile:
    def __init__(self):
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> Dict:
        if TASTE_PROFILE_FILE.exists():
            try:
                with open(TASTE_PROFILE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        return {
            'tag_scores': {},
            'favorite_authors': {},
            'history': [],
            'evolved_keywords': [],
            'updated_at': None,
            'last_decay_week': None
        }

    def save(self) -> None:
        self.data['updated_at'] = datetime.now().isoformat()
        with open(TASTE_PROFILE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def update_from_papers(self, papers: List[Dict]) -> None:
        tag_scores = self.data.get('tag_scores', {})
        fav_authors = self.data.get('favorite_authors', {})

        for paper in papers:
            score = paper.get('interest_score', 3)
            tags = paper.get('tags', [])
            authors = paper.get('authors', [])

            for tag in tags:
                tag_scores[tag] = tag_scores.get(tag, 0) + score

            if score >= 4:
                for author in authors[:3]:
                    fav_authors[author] = fav_authors.get(author, 0) + 1

        self.data['tag_scores'] = tag_scores
        self.data['favorite_authors'] = fav_authors

        self._check_evolved_keywords()

        history = self.data.get('history', [])
        today = datetime.now().strftime('%Y-%m-%d')

        scores = [p.get('interest_score', 3) for p in papers]
        avg_score = sum(scores) / len(scores) if scores else 0

        top_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)[:3]

        history.append({
            'date': today,
            'papers_fetched': len(papers),
            'papers_deep_read': sum(1 for p in papers if p.get('deep_read')),
            'avg_score': round(avg_score, 2),
            'top_tags': [t[0] for t in top_tags]
        })

        if len(history) > 90:
            history = history[-90:]

        self.data['history'] = history

        self._apply_weekly_decay()

        self.save()

    def _check_evolved_keywords(self) -> None:
        tag_scores = self.data.get('tag_scores', {})
        evolved = self.data.get('evolved_keywords', [])

        all_seed_keywords = []
        for kw_list in SEED_KEYWORDS.values():
            all_seed_keywords.extend([k.lower().replace(' ', '-') for k in kw_list])

        for tag, score in tag_scores.items():
            tag_normalized = tag.lower().replace(' ', '-')
            if score >= EVOLVED_KEYWORD_THRESHOLD:
                if tag_normalized not in all_seed_keywords and tag not in evolved:
                    evolved.append(tag)

        self.data['evolved_keywords'] = evolved

    def _apply_weekly_decay(self) -> None:
        now = datetime.now()
        week_num = now.isocalendar()[1]
        year = now.year
        current_week = f"{year}-W{week_num}"

        if self.data.get('last_decay_week') == current_week:
            return

        tag_scores = self.data.get('tag_scores', {})
        for tag in tag_scores:
            tag_scores[tag] *= TASTE_DECAY_RATE

        tag_scores = {k: v for k, v in tag_scores.items() if v >= 0.5}
        self.data['tag_scores'] = tag_scores

        self.data['last_decay_week'] = current_week

    def boost_tag(self, tag: str, amount: float = 0.5) -> None:
        """增加某个标签的兴趣权重（用户点👍）"""
        tag_scores = self.data.get('tag_scores', {})
        if tag not in tag_scores:
            tag_scores[tag] = 1.0
        tag_scores[tag] = min(10.0, tag_scores[tag] + amount)
        self.data['tag_scores'] = tag_scores

    def reduce_tag(self, tag: str, amount: float = 0.3) -> None:
        """减少某个标签的兴趣权重（用户点👎）"""
        tag_scores = self.data.get('tag_scores', {})
        if tag in tag_scores:
            tag_scores[tag] = max(0.1, tag_scores[tag] - amount)
            self.data['tag_scores'] = tag_scores

    def get_top_interests(self, n: int = 5) -> List[tuple]:
        tag_scores = self.data.get('tag_scores', {})
        return sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)[:n]

    def get_favorite_authors(self, n: int = 3) -> List[str]:
        fav = self.data.get('favorite_authors', {})
        sorted_authors = sorted(fav.items(), key=lambda x: x[1], reverse=True)[:n]
        return [a[0] for a in sorted_authors]

    def get_stats_text(self) -> str:
        top = self.get_top_interests()
        authors = self.get_favorite_authors()
        evolved = self.data.get('evolved_keywords', [])
        history = self.data.get('history', [])

        total_papers = sum(h.get('papers_fetched', 0) for h in history)
        total_deep = sum(h.get('papers_deep_read', 0) for h in history)

        text = "📊 小铁皮的学术画像\n"
        text += "━" * 20 + "\n\n"

        if top:
            text += "🔥 最感兴趣的方向：\n"
            for i, (tag, score) in enumerate(top, 1):
                text += f"  {i}. {tag} ({score:.1f}分)\n"
            text += "\n"

        if authors:
            text += f"⭐ 关注的作者：{', '.join(authors)}\n\n"

        if evolved:
            text += f"🌱 发现的新兴趣：{', '.join(evolved)}\n\n"

        text += f"📚 累计阅读：{total_papers}篇，精读{total_deep}篇\n"

        return text
