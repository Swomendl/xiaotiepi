import time
import json
import re
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from xml.etree import ElementTree as ET

from .config import (
    ARXIV_API_URL, BIORXIV_API_URL, ARXIV_CATEGORIES,
    SEED_KEYWORDS, REQUEST_DELAY, MAX_PAPERS_PER_DAY, MIN_PAPERS_PER_DAY,
    PAPER_DATA_FILE, TASTE_PROFILE_FILE, SAVE_DIR
)


class PaperFetcher:
    def __init__(self):
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        self.evolved_keywords = self._load_evolved_keywords()

    def _load_evolved_keywords(self) -> List[str]:
        if TASTE_PROFILE_FILE.exists():
            try:
                with open(TASTE_PROFILE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('evolved_keywords', [])
            except:
                pass
        return []

    def _get_all_keywords(self) -> Dict[str, List[str]]:
        keywords = {k: list(v) for k, v in SEED_KEYWORDS.items()}
        if self.evolved_keywords:
            keywords['evolved'] = self.evolved_keywords
        return keywords

    def _match_keywords(self, text: str) -> tuple:
        text_lower = text.lower()
        keywords = self._get_all_keywords()

        primary_hits = sum(1 for kw in keywords.get('primary', []) if kw.lower() in text_lower)
        tools_hits = sum(1 for kw in keywords.get('tools', []) if kw.lower() in text_lower)
        methods_hits = sum(1 for kw in keywords.get('methods', []) if kw.lower() in text_lower)
        evolved_hits = sum(1 for kw in keywords.get('evolved', []) if kw.lower() in text_lower)

        priority = primary_hits * 100 + tools_hits * 10 + methods_hits * 5 + evolved_hits * 8
        total_hits = primary_hits + tools_hits + methods_hits + evolved_hits

        return priority, total_hits

    def fetch_arxiv(self, max_results: int = 50) -> List[Dict]:
        categories = '+OR+'.join([f'cat:{cat}' for cat in ARXIV_CATEGORIES])
        params = {
            'search_query': categories,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending',
            'max_results': str(max_results)
        }

        url = f"{ARXIV_API_URL}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'xiaotiepi-paper-agent/1.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                xml_data = response.read().decode('utf-8')
        except Exception as e:
            print(f"arXiv fetch error: {e}")
            return []

        papers = []
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}

        try:
            root = ET.fromstring(xml_data)
            for entry in root.findall('atom:entry', ns):
                title_elem = entry.find('atom:title', ns)
                abstract_elem = entry.find('atom:summary', ns)
                id_elem = entry.find('atom:id', ns)

                if title_elem is None or abstract_elem is None:
                    continue

                title = ' '.join(title_elem.text.strip().split())
                abstract = ' '.join(abstract_elem.text.strip().split())
                arxiv_id = id_elem.text.strip().split('/')[-1] if id_elem is not None else ''

                authors = []
                for author in entry.findall('atom:author', ns):
                    name = author.find('atom:name', ns)
                    if name is not None:
                        authors.append(name.text.strip())

                link = f"https://arxiv.org/abs/{arxiv_id}"

                papers.append({
                    'id': f'arxiv:{arxiv_id}',
                    'title': title,
                    'authors': authors[:5],
                    'abstract': abstract,
                    'url': link,
                    'source': 'arxiv'
                })
        except Exception as e:
            print(f"arXiv parse error: {e}")

        return papers

    def fetch_biorxiv(self, days_back: int = 3) -> List[Dict]:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        url = f"{BIORXIV_API_URL}/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}/0"

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'xiaotiepi-paper-agent/1.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"bioRxiv fetch error: {e}")
            return []

        papers = []
        for item in data.get('collection', []):
            papers.append({
                'id': f"biorxiv:{item.get('doi', '')}",
                'title': item.get('title', ''),
                'authors': item.get('authors', '').split('; ')[:5],
                'abstract': item.get('abstract', ''),
                'url': f"https://www.biorxiv.org/content/{item.get('doi', '')}",
                'source': 'biorxiv'
            })

        return papers

    def filter_papers(self, papers: List[Dict]) -> List[Dict]:
        scored_papers = []

        for paper in papers:
            text = f"{paper['title']} {paper['abstract']}"
            priority, hits = self._match_keywords(text)

            if hits > 0:
                paper['_priority'] = priority
                paper['_hits'] = hits
                scored_papers.append(paper)

        scored_papers.sort(key=lambda x: x['_priority'], reverse=True)

        result = scored_papers[:MAX_PAPERS_PER_DAY]

        for p in result:
            p.pop('_priority', None)
            p.pop('_hits', None)

        return result

    def fetch_all(self) -> List[Dict]:
        print("Fetching from arXiv...")
        arxiv_papers = self.fetch_arxiv()
        print(f"Got {len(arxiv_papers)} papers from arXiv")

        time.sleep(REQUEST_DELAY)

        print("Fetching from bioRxiv...")
        biorxiv_papers = self.fetch_biorxiv()
        print(f"Got {len(biorxiv_papers)} papers from bioRxiv")

        all_papers = arxiv_papers + biorxiv_papers

        filtered = self.filter_papers(all_papers)
        print(f"After filtering: {len(filtered)} papers")

        return filtered

    def should_fetch_today(self) -> bool:
        if not PAPER_DATA_FILE.exists():
            return True

        try:
            with open(PAPER_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                last_fetch = data.get('last_fetch_date')
                if last_fetch:
                    today = datetime.now().strftime('%Y-%m-%d')
                    return last_fetch != today
        except:
            pass

        return True

    def save_papers(self, papers: List[Dict]) -> None:
        data = {
            'last_fetch_date': datetime.now().strftime('%Y-%m-%d'),
            'today_papers': papers,
            'briefing_delivered': False,
            'briefing_text': None
        }

        with open(PAPER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_today_papers(self) -> List[Dict]:
        if not PAPER_DATA_FILE.exists():
            return []

        try:
            with open(PAPER_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                today = datetime.now().strftime('%Y-%m-%d')
                if data.get('last_fetch_date') == today:
                    return data.get('today_papers', [])
        except:
            pass

        return []
