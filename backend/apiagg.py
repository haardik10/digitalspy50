import re
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

NEWSAPI_BASE_URL = "https://newsapi.org/v2"
NEWSAPI_KEY = "7e27e2a9f7604248b80561497efe22b4"

MAX_PAGE_SIZE = 100
MAX_PAGES = 5
MIN_SOURCES_PER_CLUSTER = 2
SIMILARITY_THRESHOLD = 0.25
REQUEST_TIMEOUT = 20

DOMAIN_CONFIG = {
    "general": {
        "mode": "everything",
        "params": {
            "q": "(breaking news OR world news OR economy OR business OR technology)",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": MAX_PAGE_SIZE,
        },
    },
    "finance": {
        "mode": "everything",
        "params": {
            "q": "(stock market OR finance OR economy OR inflation OR interest rates OR earnings OR nasdaq OR dow OR s&p 500)",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": MAX_PAGE_SIZE,
        },
    },
    "sports": {
        "mode": "everything",
        "params": {
            "q": "(sports OR football OR basketball OR baseball OR championship OR league)",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": MAX_PAGE_SIZE,
        },
    },
    "politics": {
        "mode": "everything",
        "params": {
            "q": "(politics OR election OR senate OR congress OR white house OR trump OR biden OR government OR policy)",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": MAX_PAGE_SIZE,
        },
    },
    "cinema": {
        "mode": "everything",
        "params": {
            "q": "(film OR movie OR cinema OR hollywood OR box office OR actor OR actress OR entertainment)",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": MAX_PAGE_SIZE,
        },
    },
}


def get_available_domains():
    return list(DOMAIN_CONFIG.keys())


def ensure_api_key():
    if not NEWSAPI_KEY:
        raise RuntimeError("NEWSAPI_KEY is missing.")


def clean_for_similarity(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = text.lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_similarity_text(article):
    title = article.get("title", "") or ""
    text = article.get("text", "") or ""
    short_text = " ".join(text.split()[:250])
    return clean_for_similarity(title + " " + short_text)


def dedupe_articles(articles):
    seen_urls = set()
    deduped = []

    for article in articles:
        url = (article.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append(article)

    return deduped


def normalize_article(raw, domain):
    source_name = "Unknown Source"
    if isinstance(raw.get("source"), dict):
        source_name = raw.get("source", {}).get("name") or "Unknown Source"

    title = (raw.get("title") or "").strip()
    description = (raw.get("description") or "").strip()
    content = (raw.get("content") or "").strip()
    url = (raw.get("url") or "").strip()

    text = " ".join(part for part in [description, content] if part).strip()

    if not title or not text or not url:
        return None

    return {
        "title": title,
        "url": url,
        "text": text,
        "source": source_name,
        "image": raw.get("urlToImage") or "",
        "domain": domain,
        "published_at": raw.get("publishedAt") or "",
    }


def fetch_newsapi_articles(domain="general"):
    ensure_api_key()

    domain = (domain or "general").strip().lower()
    config = DOMAIN_CONFIG.get(domain, DOMAIN_CONFIG["general"])

    endpoint = config["mode"]
    url = f"{NEWSAPI_BASE_URL}/{endpoint}"
    base_params = dict(config["params"])

    headers = {
        "X-Api-Key": NEWSAPI_KEY
    }

    all_articles = []

    for page in range(1, MAX_PAGES + 1):
        params = dict(base_params)
        params["page"] = page

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        payload = response.json()

        if payload.get("status") != "ok":
            raise RuntimeError(payload.get("message", "NewsAPI request failed."))

        raw_articles = payload.get("articles", []) or []

        if not raw_articles:
            break

        normalized = []
        for raw in raw_articles:
            article = normalize_article(raw, domain)
            if article:
                normalized.append(article)

        all_articles.extend(normalized)

        if len(raw_articles) < MAX_PAGE_SIZE:
            break

    return dedupe_articles(all_articles)


def group_similar_articles(articles, threshold=SIMILARITY_THRESHOLD):
    if not articles:
        return []

    docs = [build_similarity_text(article) for article in articles]

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(docs)
        sim_matrix = cosine_similarity(tfidf_matrix)
    except Exception:
        return []

    groups = []
    visited = set()

    for i in range(len(articles)):
        if i in visited:
            continue

        current_group = [i]
        visited.add(i)

        for j in range(i + 1, len(articles)):
            if j not in visited and sim_matrix[i][j] >= threshold:
                current_group.append(j)
                visited.add(j)

        groups.append(current_group)

    grouped_articles = []

    for group_id, group_indices in enumerate(groups):
        cluster = []

        for idx in group_indices:
            article = articles[idx].copy()
            article["group_id"] = group_id
            cluster.append(article)

        grouped_articles.append(cluster)

    return grouped_articles


def filter_clusters_with_min_sources(grouped_articles, min_sources=MIN_SOURCES_PER_CLUSTER):
    filtered = []

    for group in grouped_articles:
        if not group:
            continue

        unique_sources = {
            article.get("source", "").strip()
            for article in group
            if article.get("source", "").strip()
        }

        if len(unique_sources) < min_sources:
            continue

        filtered.append(group)

    return filtered


def get_latest_articles(domain="general"):
    return fetch_newsapi_articles(domain=domain)


def get_grouped_articles(domain="general"):
    articles = fetch_newsapi_articles(domain=domain)

    if not articles:
        return []

    grouped = group_similar_articles(articles, threshold=SIMILARITY_THRESHOLD)
    grouped = filter_clusters_with_min_sources(
        grouped,
        min_sources=MIN_SOURCES_PER_CLUSTER
    )

    return grouped


if __name__ == "__main__":
    domain = "general"

    try:
        articles = get_latest_articles(domain=domain)
        print(f"\nFetched {len(articles)} articles for domain: {domain}\n")

        grouped_articles = get_grouped_articles(domain=domain)
        print(f"Grouped clusters with at least {MIN_SOURCES_PER_CLUSTER} sources: {len(grouped_articles)}\n")

        for i, group in enumerate(grouped_articles, start=1):
            print(f"Group {i}")
            print("-" * 60)
            for article in group:
                print("Source:", article["source"])
                print("Title :", article["title"])
                print("URL   :", article["url"])
                print("Date  :", article["published_at"])
                print()
            print("=" * 60)

    except Exception as e:
        print("Error:", e)