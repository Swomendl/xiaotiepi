import os
import json
import re
from typing import List, Dict, Optional
from datetime import datetime

from .config import (
    ANTHROPIC_MODEL, SUMMARIZE_TEMPERATURE, CHAT_TEMPERATURE,
    SCHOLAR_SYSTEM_PROMPT, CHAT_SYSTEM_PROMPT_ADDON,
    MAX_DEEP_READ, PAPER_DATA_FILE, TASTE_PROFILE_FILE
)
from .api_key_manager import get_api_key


class PaperSummarizer:
    def __init__(self):
        self.api_key = get_api_key()
        self.client = None
        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                print("anthropic package not installed")
            except Exception as e:
                print(f"Failed to init Anthropic client: {e}")

    def _get_taste_addon(self) -> str:
        if not TASTE_PROFILE_FILE.exists():
            return ""

        try:
            with open(TASTE_PROFILE_FILE, 'r', encoding='utf-8') as f:
                taste = json.load(f)

            tag_scores = taste.get('tag_scores', {})
            if not tag_scores:
                return ""

            sorted_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)[:5]
            fav_authors = list(taste.get('favorite_authors', {}).keys())[:3]

            addon = "\n\n## 你当前的学术偏好（根据过去阅读积累）\n\n你目前最感兴趣的方向（按热度排序）：\n"
            for i, (tag, score) in enumerate(sorted_tags, 1):
                addon += f"{i}. {tag}（{score:.1f} 分）\n"

            if fav_authors:
                addon += f"\n你最近关注的作者：{', '.join(fav_authors)}\n"

            addon += "\n请在评分时参考这些偏好，但不要被它们完全束缚——如果发现了新的有趣方向，也可以给高分。"
            return addon
        except:
            return ""

    def summarize_papers(self, papers: List[Dict]) -> List[Dict]:
        if not self.client:
            return self._fallback_summarize(papers)

        papers_text = ""
        for i, p in enumerate(papers):
            papers_text += f"\n### 论文 {i+1}\n标题：{p['title']}\n摘要：{p['abstract']}\n来源：{p['source']}\n"

        system_prompt = SCHOLAR_SYSTEM_PROMPT + self._get_taste_addon()

        try:
            message = self.client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"请阅读以下{len(papers)}篇论文摘要，对每篇生成解读：\n{papers_text}"}
                ],
                temperature=SUMMARIZE_TEMPERATURE,
            )

            response_text = message.content[0].text
            summaries = self._parse_json_response(response_text)

            if len(summaries) != len(papers):
                return self._fallback_summarize(papers)

            for i, paper in enumerate(papers):
                summary = summaries[i]
                paper['title_cn'] = summary.get('title_cn', paper['title'])
                paper['summary'] = summary.get('summary', '')
                paper['comment'] = summary.get('comment', '')
                paper['interest_score'] = summary.get('interest_score', 3)
                paper['interest_reason'] = summary.get('interest_reason', '')
                paper['tags'] = summary.get('tags', [])
                paper['deep_read'] = summary.get('deep_read', False)
                paper['fetched_at'] = datetime.now().isoformat()

            deep_read_count = sum(1 for p in papers if p.get('deep_read'))
            if deep_read_count == 0:
                papers_sorted = sorted(papers, key=lambda x: x.get('interest_score', 0), reverse=True)
                for p in papers_sorted[:MAX_DEEP_READ]:
                    p['deep_read'] = True

            return papers

        except Exception as e:
            print(f"Summarize error: {e}")
            return self._fallback_summarize(papers)

    def _parse_json_response(self, text: str) -> List[Dict]:
        text = text.strip()

        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            text = json_match.group(1)

        if text.startswith('['):
            pass
        else:
            start = text.find('[')
            end = text.rfind(']')
            if start != -1 and end != -1:
                text = text[start:end+1]

        try:
            return json.loads(text)
        except:
            return []

    def _fallback_summarize(self, papers: List[Dict]) -> List[Dict]:
        for i, paper in enumerate(papers):
            paper['title_cn'] = paper['title']
            paper['summary'] = paper['abstract'][:200] + '...' if len(paper['abstract']) > 200 else paper['abstract']
            paper['comment'] = '（AI 摘要暂不可用）'
            paper['interest_score'] = 3
            paper['interest_reason'] = '自动评分'
            paper['tags'] = []
            paper['deep_read'] = i < MAX_DEEP_READ
            paper['fetched_at'] = datetime.now().isoformat()
        return papers

    def chat(self, user_message: str, papers: List[Dict], history: List[Dict] = None) -> str:
        if not self.client:
            return "抱歉，AI 服务暂时不可用 😔"

        papers_context = "\n".join([
            f"【{p.get('title_cn', p['title'])}】\n{p.get('summary', p['abstract'][:300])}\n"
            for p in papers if p.get('deep_read') or p.get('interest_score', 0) >= 4
        ])

        system_prompt = SCHOLAR_SYSTEM_PROMPT + CHAT_SYSTEM_PROMPT_ADDON + f"\n\n## 今日论文上下文\n\n{papers_context}"

        messages = []
        if history:
            for h in history[-10:]:
                messages.append({"role": h['role'], "content": h['content']})
        messages.append({"role": "user", "content": user_message})

        try:
            message = self.client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
                temperature=CHAT_TEMPERATURE,
            )
            return message.content[0].text
        except Exception as e:
            return f"出错了：{e}"

    def save_summarized_papers(self, papers: List[Dict]) -> None:
        data = {
            'last_fetch_date': datetime.now().strftime('%Y-%m-%d'),
            'today_papers': papers,
            'briefing_delivered': False,
            'briefing_text': None
        }

        with open(PAPER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
