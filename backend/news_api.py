import feedparser
from newspaper import Article
from urllib.parse import urlparse, urlunparse

RSS_FEEDS = [
    'https://www.reutersagency.com/feed/?best-topics=news',
    'https://apnews.com/rss',
    'https://rss.dw.com/xml/rss-en-all',
    'https://www.france24.com/en/rss',
]

MAX_PER_FEED = 5


def normalize_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
    except Exception:
        return url


def extract_source(entry, parsed_feed) -> str:
    source = entry.get("source")
    if isinstance(source, dict):
        return source.get("title", "") or parsed_feed.feed.get("title", "Unknown Source")
    return parsed_feed.feed.get("title", "Unknown Source")


def extract_image(entry, article) -> str:
    image = article.top_image

    if not image:
        media = entry.get("media_content")
        if isinstance(media, list) and len(media) > 0:
            image = media[0].get("url")

    if not image:
        thumb = entry.get("media_thumbnail")
        if isinstance(thumb, list) and len(thumb) > 0:
            image = thumb[0].get("url")

    if not image or not isinstance(image, str) or not image.startswith("http"):
        image = "/static/no-image.png"

    return image


def get_trending_news():
    articles_out = []
    seen = set()

    for feed_url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)

            if getattr(parsed, "bozo", 0):
                print(f"Warning: malformed feed -> {feed_url}")

            entries = parsed.entries[:MAX_PER_FEED]

            for entry in entries:
                url = entry.get("link")
                if not url:
                    continue

                clean_url = normalize_url(url)
                if clean_url in seen:
                    continue

                source = extract_source(entry, parsed)
                fallback_title = entry.get("title", "Untitled")

                try:
                    article = Article(url)
                    article.download()
                    article.parse()

                    text = article.text.strip() if article.text else ""
                    title = article.title.strip() if article.title else fallback_title
                    image = extract_image(entry, article)

                    if not text:
                        continue

                    articles_out.append({
                        "title": title,
                        "url": clean_url,
                        "text": text,
                        "source": source,
                        "image": image
                    })

                    seen.add(clean_url)

                except Exception as err:
                    print(f"Failed article parse: {url} -> {err}")
                    continue

        except Exception as err:
            print(f"Failed feed parse: {feed_url} -> {err}")
            continue

    return articles_out