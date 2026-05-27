import feedparser
import requests
from urllib.parse import quote
from collections import defaultdict


ACADEMIC_QUERIES = [
    "AI agents human communication",
    "generative AI communication",
    "AI mediated communication",
    "human AI interaction meaning making",
    "human AI interaction user agency",
    "agentic AI interface user experience",
    "AI agents user control",
    "AI companions social interaction",
    "AI chatbots self disclosure",
    "generative AI education disclosure",
    "fediverse governance",
    "Mastodon moderation",
    "decentralized social media governance",
    "platform governance social media",
    "content moderation decentralized platforms",
]


TOP_JOURNALS = [
    "New Media & Society",
    "Social Media + Society",
    "Information Communication & Society",
    "Journal of Computer-Mediated Communication",
    "Communication Research",
    "Digital Journalism",
    "Media Culture & Society",
    "Big Data & Society",
    "Human-Computer Interaction",
    "ACM Transactions on Computer-Human Interaction",
    "Proceedings of the ACM on Human-Computer Interaction",
    "CHI Conference on Human Factors in Computing Systems",
    "Computer Supported Cooperative Work",
]


REQUIRED_ACADEMIC_TERMS = [
    "communication",
    "social media",
    "platform",
    "governance",
    "content moderation",
    "fediverse",
    "mastodon",
    "decentralized",
    "federated",
    "human-ai interaction",
    "human ai interaction",
    "hci",
    "user experience",
    "user agency",
    "user control",
    "meaning making",
    "self-disclosure",
    "self disclosure",
    "ai companion",
    "ai companions",
    "chatbot",
    "generative ai",
    "ai agent",
    "ai agents",
    "agentic ai",
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

    # Singapore / policy
    "CNA Singapore": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml",
    "Gov.sg": "https://www.gov.sg/rss",
    "MAS Singapore": "https://www.mas.gov.sg/rss/news",

    # Chambana
    "Illinois News Bureau": "https://news.illinois.edu/view/rss/6367",
    "Smile Politely": "https://www.smilepolitely.com/feed/",
    "WCIA": "https://www.wcia.com/feed/",
}


MAX_ITEMS_PER_SOURCE_PER_SECTION = 3


def is_relevant_academic_paper(item):
    text = (
        item.get("title", "") + " " +
        item.get("summary", "") + " " +
        item.get("query", "")
    ).lower()

    return any(term in text for term in REQUIRED_ACADEMIC_TERMS)


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


def fetch_semantic_scholar_papers(limit_per_query=5):
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
                "query": query,
                "citation_count": item.get("citationCount", 0),
            })

    return papers


def fetch_crossref_query(query, rows=3):
    papers = []

    url = "https://api.crossref.org/works"

    params = {
        "query": query,
        "rows": rows,
        "sort": "published",
        "order": "desc",
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
    except requests.RequestException:
        return papers

    data = response.json()

    for item in data.get("message", {}).get("items", []):
        title_list = item.get("title", [])
        title = title_list[0] if title_list else ""

        doi = item.get("DOI", "")
        link = f"https://doi.org/{doi}" if doi else item.get("URL", "")

        container = item.get("container-title", [])
        journal = container[0] if container else ""

        abstract = item.get("abstract", "")

        papers.append({
            "source": f"Crossref · {journal}" if journal else "Crossref",
            "title": title.strip(),
            "link": link,
            "summary": abstract,
            "category": "Academic Papers",
            "query": query,
        })

    return papers


def fetch_crossref_papers(limit_per_query=3):
    papers = []

    for query in ACADEMIC_QUERIES:
        papers.extend(fetch_crossref_query(query, limit_per_query))

    targeted_terms = [
        "fediverse",
        "Mastodon",
        "decentralized social media",
        "federated social media",
        "agentic AI",
        "AI agents",
        "human-AI interaction",
    ]

    for journal in TOP_JOURNALS:
        for term in targeted_terms:
            combined_query = f"{term} {journal}"
            papers.extend(fetch_crossref_query(combined_query, 2))

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

    academic_items = []
    academic_items.extend(fetch_arxiv_papers())
    academic_items.extend(fetch_semantic_scholar_papers())
    academic_items.extend(fetch_crossref_papers())

    academic_items = [
        item for item in academic_items
        if is_relevant_academic_paper(item)
    ]

    items.extend(academic_items)
    items.extend(fetch_news())

    items = deduplicate_items(items)
    items = limit_source_dominance(items)

    return items
