from flask import Flask, jsonify, render_template
from flask_cors import CORS
import os
import re

from backend.news_api import get_trending_news
from backend.aggregator import get_latest_articles
from backend.distilbert_model import predict_news

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, '../templates'),
    static_folder=os.path.join(BASE_DIR, '../static')
)
CORS(app)


def summarize_text(text, max_sentences=3):
    if not isinstance(text, str) or not text.strip():
        return "No summary available."

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]

    if not sentences:
        short_text = text[:300].strip()
        return short_text + "..." if len(text) > 300 else short_text

    summary = " ".join(sentences[:max_sentences])

    if len(summary) > 500:
        summary = summary[:500].rsplit(" ", 1)[0] + "..."

    return summary


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/trending')
def trending():
    return render_template('trending.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/api/fetch-and-classify', methods=['GET'])
def fetch_and_classify():
    try:
        articles = get_latest_articles()
        results = []

        for article in articles:
            text = article.get('text', '').strip()

            if not text:
                continue

            pred = predict_news(text)
            summary = summarize_text(text)

            results.append({
                'title': article.get('title', 'Untitled'),
                'url': article.get('url', ''),
                'source': article.get('source', 'Unknown Source'),
                'image': article.get('image', '/static/no-image.png'),
                'prediction': pred.get('prediction', 'Unknown'),
                'confidence': pred.get('confidence', 0),
                'summary': summary
            })

        return jsonify(results)

    except Exception as e:
        return jsonify({
            "error": str(e),
            "results": []
        }), 500


@app.route('/api/trending-news', methods=['GET'])
def trending_news():
    try:
        articles = get_trending_news()
        results = []

        for article in articles:
            text = (article.get("title", "") + " " + article.get("text", "")).strip()

            pred = predict_news(text) if text else {
                
            }

            results.append({
                "title": article.get("title", "Untitled"),
                "url": article.get("url", ""),
                "source": article.get("source", "Unknown"),
                "image": article.get("image", "/static/no-image.png"),
                
                "summary": summarize_text(article.get("text", ""))
            })

        return jsonify(results)

    except Exception as e:
        return jsonify({
            "error": str(e),
            "results": []
        }), 500


if __name__ == '__main__':
    app.run(debug=True)