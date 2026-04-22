import random
import os
import json
import re
import feedparser
from newspaper import Article, Config

# =========================================================
# CONFIG
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# your new formatted file
API_JSON_PATH = os.path.join(BASE_DIR, "apiarticles.json")

MAX_PER_FEED = 10

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

# =========================================================
# DOMAIN CONFIG
# =========================================================
DOMAIN_KEYWORDS = {
    "general": ["breaking", "world", "economy", "business", "technology"],
    "finance": ["stock", "finance", "economy", "inflation", "earnings", "market", "nasdaq", "dow"],
    "sports": ["sports", "football", "cricket", "league", "match", "tournament"],
    "politics": ["politics", "election", "government", "policy", "senate", "congress", "white house"],
    "cinema": ["film", "movie", "entertainment", "actor", "actress", "hollywood", "box office"]
}

# map frontend domain names to JSON category names


DOMAIN_FEEDS = {
    "general": [

"https://www.axios.com/feed.xml",
"https://www.vox.com/rss/index.xml",
"https://www.usatoday.com/rss/",
"https://www.cbsnews.com/latest/rss/main",
    ],

    "finance": [
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",

"https://www.ft.com/rss/home",
"https://www.investing.com/rss/news.rss",
"https://www.marketwatch.com/rss/topstories",
"https://www.fool.com/feeds/index.aspx"
    ],

    "sports": [
        "http://feeds.bbci.co.uk/sport/rss.xml",
        "https://www.theguardian.com/sport/rss",
        "https://www.reutersagency.com/feed/?best-topics=sports",
        "https://feeds.bbci.co.uk/sport/football/rss.xml",
    ],

    "politics": [
        


"https://www.foxnews.com/politics/feed",
"https://feeds.npr.org/1014/rss.xml",
"https://abcnews.go.com/abcnews/politicsheadlines"
    ],

    "cinema": [
        



"https://www.slashfilm.com/feed/",
"https://www.collider.com/rss/",

"https://www.etonline.com/news/rss",

    ]
}

# =========================================================
# HELPERS
# =========================================================
def clean_text(text):
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", text).strip().lower()


def dedupe_articles(articles):
    seen_urls = set()
    cleaned = []

    for article in articles:
        url = str(article.get("url", "")).strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        cleaned.append(article)

    return cleaned


def matches_domain(article, domain):
    domain = (domain or "general").strip().lower()
    keywords = DOMAIN_KEYWORDS.get(domain, DOMAIN_KEYWORDS["general"])

    title = clean_text(article.get("title", ""))
    description = clean_text(article.get("description", ""))
    text = clean_text(article.get("text", ""))

    combined = f"{title} {description} {text}"

    if domain == "general":
        return True

    return any(keyword in combined for keyword in keywords)


def normalize_api_article(a):
    title = a.get("title", "")
    url = a.get("url", "")

    if not title or not url:
        return None

    return {
        "title": title,
        "description": a.get("description", "") or "",
        "text": a.get("content", "") or "",
        "url": url,
        "source": a.get("source", {}).get("name", "") if isinstance(a.get("source"), dict) else "",
        "image": a.get("urlToImage", "") or "",
        "published_at": a.get("publishedAt", "") or "",
        "source_type": "api_json"
    }


# =========================================================
# API JSON FETCH
# =========================================================
def fetch_api_json_articles(domain="general"):
    if not os.path.exists(API_JSON_PATH):
        raise FileNotFoundError(f"final_categorized_news.json not found at: {API_JSON_PATH}")

    with open(API_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    categories = data.get("categories", {})
    domain = (domain or "general").strip().lower()

    category_block = categories.get(domain, {})
    raw_articles = category_block.get("articles", [])

    # shuffle only inside general category
    if domain == "general":
        raw_articles = raw_articles[:]   # make a copy so original JSON order is untouched
        random.shuffle(raw_articles)

    parsed_articles = []

    for a in raw_articles:  
        article = normalize_api_article(a)
        if article:
            parsed_articles.append(article)

    return dedupe_articles(parsed_articles)

# =========================================================
# RSS FETCH
# =========================================================
def fetch_rss_articles(domain="general"):
    feeds = DOMAIN_FEEDS.get(domain, DOMAIN_FEEDS["general"])

    if not feeds:
        return []

    config = Config()
    config.browser_user_agent = USER_AGENT

    articles = []

    for feed in feeds:
        try:
            parsed = feedparser.parse(feed)
        except Exception as e:
            print(f"RSS parse failed for {feed}: {e}")
            continue

        feed_title = parsed.feed.get("title", "")

        for entry in parsed.entries[:MAX_PER_FEED]:
            url = entry.get("link", "") or ""
            if not url:
                continue

            entry_title = entry.get("title", "") or ""
            entry_summary = (
                entry.get("summary", "")
                or entry.get("description", "")
                or ""
            ).strip()

            published_at = entry.get("published", "") or entry.get("updated", "") or ""

            try:
                article_obj = Article(url, config=config)
                article_obj.download()
                article_obj.parse()

                text = (article_obj.text or "").strip()

                if len(text.split()) < 30:
                    continue

                article = {
                    "title": article_obj.title or entry_title,
                    "description": entry_summary,
                    "text": text,
                    "url": url,
                    "source": feed_title,
                    "image": article_obj.top_image or "",
                    "published_at": published_at,
                    "source_type": "rss"
                }

                if article["title"] and article["text"] and matches_domain(article, domain):
                    articles.append(article)

            except Exception as e:
                print(f"Skipped RSS article: {url} | {e}")
                continue

    return dedupe_articles(articles)

def get_rss_only_articles(domain="general"):
    return fetch_rss_articles(domain)

# =========================================================
# COMBINED FETCH
# =========================================================
def get_all_articles(domain="general"):
    api_data = fetch_api_json_articles(domain)
    rss_data = fetch_rss_articles(domain)

    combined = api_data + rss_data
    combined = dedupe_articles(combined)
    random.shuffle(combined) 

    return combined


# =========================================================
# TEST
# =========================================================
if __name__ == "__main__":
    domain = "general"   # try: general, finance, politics, cinema, crypto
    data = get_all_articles(domain)

    print(f"Fetched {len(data)} articles for domain: {domain}\n")

    for a in data[:10]:
        print(a["source_type"], "|", a["source"], "|", a["title"])