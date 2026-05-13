import feedparser
import requests
from urllib.parse import quote


ACADEMIC_QUERIES = [
    "decentralized social media",
    "federated social media",
    "fediverse governance",
    "Mastodon governance",
    "agentic AI interface",
    "AI agents human computer interaction",
    "human AI interaction agents",
]


NEWS_FEEDS = {
    "OpenAI News": "https://openai.com/news/rss.xml",
    "Google DeepMind Blog": "https://deepmind.google/blog/rss.xml",
    "MIT Technology Review": "https://www.technologyreview.com/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "CNA Singapore": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml",
}


def fetch_arxiv_papers(limit_per_query=3):
    papers = []

    for query in ACADEMIC_QUERIES:
        url = (
            "http://export.arxiv.org/api/query?"
            f"search_query=all:{quote(query)}"
            f"&start=0&max_results={limit_per_query}"
            "&sortBy=submittedDate&sortOrder=descending"
        )

        feed = feedparser.parse(url)

        for entry in feed.entries:
            papers.append({
                "source": "arXiv",
                "title": entry.get("title", "").replace("\n", " ").strip(),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "").replace("\n", " ").strip(),
                "category": "Academic Papers",
            })

    return papers


def fetch_semantic_scholar_papers(limit_per_query=3):
    papers = []

    for query in ACADEMIC_QUERIES:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"

        params = {
            "query": query,
            "limit": limit_per_query,
            "fields": "title,abstract,url,year,authors,citationCount,publicationDate",
        }

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
        except requests.RequestException:
            continue

        data = response.json()

        for item in data.get("data", []):
            papers.append({
                "source": "Semantic Scholar",
                "title": item.get("title", "").strip(),
                "link": item.get("url", ""),
                "summary": item.get("abstract", "") or "",
                "category": "Academic Papers",
            })

    return papers


def fetch_news(limit_per_source=5):
    items = []

    for source, url in NEWS_FEEDS.items():
        feed = feedparser.parse(url)

        for entry in feed.entries[:limit_per_source]:
            items.append({
                "source": source,
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "").strip(),
                "category": "News",
            })

    return items


def collect_items():
    items = []
    items.extend(fetch_arxiv_papers())
    items.extend(fetch_semantic_scholar_papers())
    items.extend(fetch_news())

    seen_titles = set()
    unique_items = []

    for item in items:
        title = item["title"].lower().strip()

        if not title:
            continue

        if title not in seen_titles:
            seen_titles.add(title)
            unique_items.append(item)

    return unique_items
    