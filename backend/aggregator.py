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
            try:
                article = Article(url)
                article.download()
                article.parse()
                text = article.text
                title = article.title or e.get('title')
                out.append({'title': title, 'url': url, 'text': text, 'source': source})
            except Exception:
                continue
    # dedupe by url
    seen = set()
    deduped = []
    for a in out:
        if a['url'] in seen: continue
        seen.add(a['url'])
        deduped.append(a)
    return deduped
