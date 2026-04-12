import feedparser
from newspaper import Article

RSS_FEEDS = [
    'http://feeds.bbci.co.uk/news/rss.xml',
    'https://rss.cnn.com/rss/edition.rss',
    'https://timesofindia.indiatimes.com/rssfeedstopstories.cms'
]

MAX_PER_FEED = 5


def get_latest_articles():
    out = []

    for feed in RSS_FEEDS:
        parsed = feedparser.parse(feed)
        entries = parsed.entries[:MAX_PER_FEED]

        for e in entries:
            url = e.get('link')
            source = e.get('source', {}).get('title', '') or parsed.feed.get('title', '')

            if not url:
                continue

            try:
                article = Article(url)
                article.download()
                article.parse()

                text = article.text.strip()
                title = article.title or e.get('title', 'Untitled')

                # 🔥 IMAGE EXTRACTION (main fix)
                image = article.top_image

                # fallback if newspaper fails
                if not image:
                    media = e.get('media_content') or e.get('media_thumbnail')
                    if media and isinstance(media, list):
                        image = media[0].get('url')

                # fallback if still empty
                if not image:
                    image = "https://via.placeholder.com/400x250?text=No+Image"

                if not text:
                    continue

                out.append({
                    'title': title,
                    'url': url,
                    'text': text,
                    'source': source,
                    'image': image
                })

            except Exception:
                continue

    # 🔁 dedupe by URL
    seen = set()
    deduped = []

    for a in out:
        if a['url'] in seen:
            continue
        seen.add(a['url'])
        deduped.append(a)

    return deduped