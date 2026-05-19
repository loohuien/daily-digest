import feedparser
import requests
from urllib.parse import quote
from collections import defaultdict


ACADEMIC_QUERIES = [
    '"decentralized social media" governance',
    '"federated social media" moderation',
    '"fediverse" governance',
    '"Mastodon" content moderation',
    '"platform decentralization" social media',
    '"protocol governance" social media',
    '"agentic AI" interface',
    '"AI agents" "human-computer interaction"',
    '"agentic interface" "user control"',
    '"AI agents" "user agency"',
    '"human-AI interaction" "AI agents"',
]


NEWS_FEEDS = {
    # AI labs
    "OpenAI News": "https://openai.com/news/rss.xml",
    "Google DeepMind Blog": "https://deepmind.google/blog/rss.xml",
    "Anthropic News": "https://www.anthropic.com/news/rss.xml",

    # Tech news
    "MIT Technology Review": "https://www.technologyreview.com/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "WIRED AI": "https://www.wired.com/feed/tag/ai/latest/rss",

    # Singapore news / policy
    "CNA Singapore": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml",
    "Gov.sg": "https://www.gov.sg/rss",
    "MAS Singapore": "https://www.mas.gov.sg/rss/news",

    # Chambana / Illinois
    "Illinois News Bureau": "https://news.illinois.edu/view/rss/6367",
    "Smile Politely": "https://www.smilepolitely.com/feed/",
    "WCIA": "https://www.wcia.com/feed/",
}


MAX_ITEMS_PER_SOURCE_PER_SECTION = 2


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
                "query": query,
            })

    return papers


def fetch_semantic_scholar_papers(limit_per_query=3):
    papers = []

    for query in ACADEMIC_QUERIES:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"

        params = {
            "query": query.replace('"', ""),
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
                "query": query,
                "citation_count": item.get("citationCount", 0),
            })

    return papers


def fetch_crossref_papers(limit_per_query=3):
    papers = []

    for query in ACADEMIC_QUERIES:
        url = "https://api.crossref.org/works"

        params = {
            "query": query.replace('"', ""),
            "rows": limit_per_query,
            "sort": "published",
            "order": "desc",
        }

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
        except requests.RequestException:
            continue

        data = response.json()

        for item in data.get("message", {}).get("items", []):
            title_list = item.get("title", [])
            title = title_list[0] if title_list else ""

            doi = item.get("DOI", "")
            link = f"https://doi.org/{doi}" if doi else item.get("URL", "")

            abstract = item.get("abstract", "")

            papers.append({
                "source": "Crossref",
                "title": title.strip(),
                "link": link,
                "summary": abstract,
                "category": "Academic Papers",
                "query": query,
            })

    return papers


def fetch_news(limit_per_source=6):
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


def classify_section(item):
    source = item.get("source", "")
    category = item.get("category", "")

    if category == "Academic Papers":
        return "Academic Papers"

    if any(x in source for x in ["OpenAI", "Anthropic", "DeepMind"]):
        return "AI Labs"

    if any(x in source for x in ["CNA", "Gov.sg", "MAS"]):
        return "Singapore Policy"

    if any(x in source for x in ["Illinois", "Smile Politely", "WCIA"]):
        return "Chambana News"

    if any(x in source for x in ["Verge", "Technology Review", "Ars Technica", "WIRED"]):
        return "Tech News"

    return "Other News"


def deduplicate_items(items):
    seen_titles = set()
    unique_items = []

    for item in items:
        title = item.get("title", "").lower().strip()

        if not title:
            continue

        if title in seen_titles:
            continue

        seen_titles.add(title)
        unique_items.append(item)

    return unique_items


def limit_source_dominance(items):
    counts = defaultdict(int)
    balanced = []

    for item in items:
        section = classify_section(item)
        source = item.get("source", "")
        key = (section, source)

        if counts[key] >= MAX_ITEMS_PER_SOURCE_PER_SECTION:
            continue

        counts[key] += 1
        balanced.append(item)

    return balanced


def collect_items():
    items = []

    items.extend(fetch_arxiv_papers())
    items.extend(fetch_semantic_scholar_papers())
    items.extend(fetch_crossref_papers())
    items.extend(fetch_news())

    items = deduplicate_items(items)
    items = limit_source_dominance(items)

    return items
