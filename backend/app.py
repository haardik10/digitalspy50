import feedparser
from newspaper import Article
from urllib.parse import urlparse, urlunparse

import os
import re
import pickle
import nltk
import numpy as np
import torch
import torch.nn as nn

from flask import Flask, jsonify, request
from flask_cors import CORS

from transformers import DistilBertTokenizerFast, DistilBertModel
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.aggregator1 import get_all_articles
from backend.distilbert_model import predict_news
from backend.news_trending import get_trending_news

# ======================================================
# APP SETUP
# ======================================================
app = Flask(__name__)
CORS(app)


# ======================================================
# PATHS
# ======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DISTILBERT_MODEL_PATH = r"C:\Users\Sovit\Downloads\NewsVeriFy_Flask-main\NewsVeriFy_Flask-main\hybrid_distilbert_cased_ihopefinal.pt"
LSTM_MODEL_PATH = os.path.join(BASE_DIR, "saved_models", "lstm_model.h5")
LSTM_TOKENIZER_PATH = os.path.join(BASE_DIR, "saved_models", "tokenizer.pkl")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"✅ DistilBERT using device: {DEVICE}")


# ======================================================
# NLTK SETUP
# ======================================================
nltk.download("stopwords", quiet=True)
try:
    nltk.download("wordnet", quiet=True)
except Exception:
    pass

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()


# ======================================================
# DISTILBERT MODEL
# ======================================================
distilbert_tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-cased")


class DistilBertHybrid(nn.Module):
    def __init__(self, num_numeric_features=12, dropout_rate=0.3):
        super().__init__()
        self.bert = DistilBertModel.from_pretrained("distilbert-base-cased")
        self.numeric_layer = nn.Sequential(
            nn.Linear(num_numeric_features, 16),
            nn.ReLU(),
            nn.Dropout(dropout_rate)
        )
        self.classifier = nn.Sequential(
            nn.Linear(self.bert.config.hidden_size + 16, 64),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(64, 2)
        )

    def forward(self, input_ids, attention_mask, numeric_feats=None):
        bert_output = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = bert_output.last_hidden_state[:, 0]

        if numeric_feats is not None:
            numeric_output = self.numeric_layer(numeric_feats)
        else:
            numeric_output = torch.zeros(
                pooled_output.size(0), 16, device=pooled_output.device
            )

        combined = torch.cat((pooled_output, numeric_output), dim=1)
        logits = self.classifier(combined)
        return {"logits": logits}


distilbert_model = None

def load_distilbert_model():
    global distilbert_model

    if distilbert_model is not None:
        return distilbert_model

    if not os.path.exists(DISTILBERT_MODEL_PATH):
        raise FileNotFoundError(f"DistilBERT model file not found at: {DISTILBERT_MODEL_PATH}")

    print("Starting model load...")
    model = DistilBertHybrid(num_numeric_features=12)
    print("Model architecture created")

    state_dict = torch.load(DISTILBERT_MODEL_PATH, map_location=DEVICE)
    print("State dict loaded")

    missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
    print("State dict applied")

    model.to(DEVICE)
    model.eval()
    print("Model fully loaded and ready")

    distilbert_model = model
    return distilbert_model


# ======================================================
# LSTM MODEL
# ======================================================
lstm_model = None
lstm_tokenizer = None

def load_lstm_model_and_tokenizer():
    global lstm_model, lstm_tokenizer

    if lstm_model is not None and lstm_tokenizer is not None:
        return lstm_model, lstm_tokenizer

    if not os.path.exists(LSTM_MODEL_PATH):
        raise FileNotFoundError(f"LSTM model file not found at: {LSTM_MODEL_PATH}")

    if not os.path.exists(LSTM_TOKENIZER_PATH):
        raise FileNotFoundError(f"LSTM tokenizer file not found at: {LSTM_TOKENIZER_PATH}")

    model = load_model(LSTM_MODEL_PATH)
    with open(LSTM_TOKENIZER_PATH, "rb") as f:
        tokenizer = pickle.load(f)

    lstm_model = model
    lstm_tokenizer = tokenizer
    return lstm_model, lstm_tokenizer


# ======================================================
# CLEANING PIPELINE FOR DISTILBERT
# ======================================================
def distilbert_cased_clean(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s.,!?&]", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def clean_publishers_and_promos(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+|www\.\S+|pic\.twitter\.com\S+|@\w+", "", text)
    text = re.sub(
        r"(?i)\b("
        r"read\s*more|continue\s*reading|subscribe|become\s*a\s*member|support\s+21wire|join\s*now|donate|"
        r"follow\s*us|watch\s*live|visit\s*our\s*site|learn\s*more|for\s*full\s*story|read\s*the\s*full\s*story|"
        r"support\s*our\s*work|subscribe\s*and\s*become|register\s*here"
        r")\b.*",
        "",
        text
    )
    agency_pattern = (
        r"(?i)\b("
        r"Reuters|Associated\s*Press|AP|AFP|BBC|CNN|MSNBC|NBC|ABC|CBS|"
        r"Fox\s*News|FOX\d{2,}|Fox\d{2,}|NYT|New\s+York\s+Times|"
        r"The\s+Times|Bloomberg|WSJ|Wall\s+Street\s+Journal|Guardian|"
        r"Politico|Newsmax|The\s+Hill|USA\s*Today|Time\s*Magazine|"
        r"Al\s*Jazeera|Sky\s*News|HuffPost|Daily\s*Mail|BuzzFeed|"
        r"NPR|CNBC|Breaking911|Infowars|Wsvn|Wftv|Cbsnews|Fox35|"
        r"TeaPainUSA|RobbinSimmons7|LWOSmwilson1113|RunBeast|NFB|"
        r"PiinkyPants1|SusannG|Mugrage|ShannonMugrage|"
        r"21WIRE|21st\s*Century\s*Wire|CONSORTIUM\s*NEWS|"
        r"POLITICO\s*Morning\s*Consult|WIRED\s*FILES|DAILY\s*SHOOTER|"
        r"CNNREAD|BBCNEWS|NBCNEWS|CBSNEWS"
        r")\b"
    )
    text = re.sub(agency_pattern, "", text)
    text = re.sub(r"(?i)\b(NEWS\s+AT\s+[A-Z0-9\s]+|FILESREAD\s+MORE|WIRE\s+\w+FILES)\b", "", text)
    text = re.sub(r"\b\d{3,4}\s*(AM|PM|EDT|EST|GMT|UTC)\b", "", text)
    text = re.sub(r"bit\.ly\S+|tinyurl\S+|t\.co\S+", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def remove_agency_variants(text):
    if not isinstance(text, str):
        return ""
    pattern = (
        r"(?i)([a-z0-9_-]*)(?:"
        r"reuters?|bbc|cnn|nbc|fox|ap|associated\s*press|bloomberg|guardian|politico|"
        r"newsmax|hill|npr|buzzfeed|al\s*jazeera|huffpost|nytimes?|washington\s*post|"
        r"usa\s*today|msnbc|abc|cbs|pbs|axios|forbes|insider|telegraph|economist|vox|"
        r"slate|daily\s*mail|time\s*magazine|new\s*yorker|wall\s*street\s*journal|wsj|"
        r"21wire|infowars|breitbart|oann|the\s*sun|mirror|dailymirror|independent|"
        r"sky\s*news|evening\s*standard|express|metro|newsweek|cnbc|cnet|espn|"
        r"dw|rtl|deccan\s*chronicle|times\s*of\s*india|hindustan\s*times|"
        r"indian\s*express|ndtv|ani|republic\s*tv|zee\s*news|abp\s*news"
        r")([a-z0-9_-]*)"
    )
    cleaned = re.sub(pattern, " ", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned


def remove_prefix_suffix_jargon(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"(?i)\b(by|reporting\s+by|editing\s+by|filed\s+by|with\s+reporting\s+by)\b[^.]{0,120}\.", " ", text)
    text = re.sub(r"^[A-Z\s]+\(Reuters\)\s*[-–]\s*", "", text)
    text = re.sub(r"\(This\s+story[^)]*\)", "", text)
    text = re.sub(r"(?i)©\s*\d{4}[^.]*all rights reserved.*$", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


REMOVE_PATTERN = r"(?i)\b(source:|more on this|read full story|copyright|\(ap\)|\(afp\))[^.]*\.?"

def final_normalize_series(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"(https?:\/\/|www\.|\.com|\.co\.uk|\.in)\S*", "", text)
    text = re.sub(REMOVE_PATTERN, "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def full_clean_pipeline(text):
    text = distilbert_cased_clean(text)
    text = clean_publishers_and_promos(text)
    text = remove_agency_variants(text)
    text = remove_prefix_suffix_jargon(text)
    text = final_normalize_series(text)
    return text

def build_short_summary(text, max_sentences=2, max_chars=220):
    if not isinstance(text, str) or not text.strip():
        return ""

    # 🔥 REMOVE HTML TAGS
    text = re.sub(r"<[^>]+>", " ", text)

    # 🔥 REMOVE HTML ENTITIES like &nbsp;
    text = re.sub(r"&[a-zA-Z]+;", " ", text)

    # 🔥 REMOVE [ +XXXX chars ] junk
    text = re.sub(r"\[\+\d+\s*chars\]", "", text)

    # 🔥 NORMALIZE SPACING
    cleaned = re.sub(r"\s+", " ", text).strip()

    # SPLIT INTO SENTENCES
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        short = cleaned[:max_chars].strip()
        return short + "..." if len(cleaned) > max_chars else short

    summary = " ".join(sentences[:max_sentences]).strip()

    if len(summary) > max_chars:
        summary = summary[:max_chars].rsplit(" ", 1)[0].strip() + "..."

    return summary

# ======================================================
# LSTM CLEANING
# ======================================================
def clean_text_lstm(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z]", " ", text)
    text = text.lower()
    tokens = [lemmatizer.lemmatize(t) for t in text.split() if t not in stop_words]
    return " ".join(tokens)


def prepare_input_lstm(tokenizer, text, max_len=300):
    cleaned = clean_text_lstm(text)
    seq = tokenizer.texts_to_sequences([cleaned])
    padded = pad_sequences(seq, maxlen=max_len)
    return padded, cleaned


# ======================================================
# MODEL PREDICTIONS
# ======================================================
def predict_distilbert(text):
    if not isinstance(text, str) or not text.strip():
        return {
            "label": "Unknown",
            "confidence": 0.0,
            "raw_score": 0.0,
            "cleaned_text": "",
            "color": "gray"
        }

    model = load_distilbert_model()
    cleaned_text = full_clean_pipeline(text)

    inputs = distilbert_tokenizer(
        cleaned_text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=384
    )
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

    with torch.inference_mode():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs["logits"], dim=1)
        confidence_tensor, pred_class = torch.max(probs, dim=1)

    confidence = float(confidence_tensor.item()) * 100
    raw_score = float(probs[0][1].item())

    if pred_class.item() == 1:
        label = "REAL"
        color = "green"
    else:
        label = "FAKE"
        color = "red"

    return {
        "label": label,
        "confidence": round(confidence, 2),
        "raw_score": round(raw_score, 4),
        "cleaned_text": cleaned_text,
        "color": color
    }


def predict_lstm(text, max_len=300, positive_label="REAL"):
    if not isinstance(text, str) or not text.strip():
        return {
            "label": "Unknown",
            "confidence": 0.0,
            "raw_score": 0.0,
            "cleaned_text": ""
        }

    model, tokenizer = load_lstm_model_and_tokenizer()
    padded, cleaned = prepare_input_lstm(tokenizer, text, max_len=max_len)

    score = float(model.predict(padded, verbose=0)[0][0])

    if score >= 0.5:
        label = positive_label
        confidence = score * 100
    else:
        label = "FAKE" if positive_label == "REAL" else "REAL"
        confidence = (1 - score) * 100

    return {
        "label": label,
        "confidence": round(confidence, 2),
        "raw_score": round(score, 4),
        "cleaned_text": cleaned
    }


# ======================================================
# PREPROCESS ARTICLES
# ======================================================
def preprocess_articles(articles):
    processed = []

    for article in articles:
        title = str(article.get("title", "")).strip()
        url = str(article.get("url", "")).strip()
        source = str(article.get("source", "")).strip()
        image = str(article.get("image", "")).strip()
        published_at = str(article.get("published_at", "")).strip()

        raw_text = str(article.get("text", "") or "").strip()
        combined_text = f"{title}. {raw_text}".strip()

        if not title or not url or not combined_text:
            continue

        standard_cleaned = full_clean_pipeline(combined_text)
        standard_cleaned = re.sub(r"\s+", " ", standard_cleaned).strip()

        if len(standard_cleaned.split()) < 20:
            continue

        processed.append({
    "title": title,
    "url": url,
    "source": source,
    "image": image,
    "published_at": published_at,
    "text": raw_text,
    "summary": build_short_summary(raw_text or combined_text),
    "combined_text": combined_text,
    "cleaned_text": standard_cleaned
})

    return processed


# ======================================================
# SIMILARITY GROUPING
# ======================================================
import re

STOP_WORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "has", "had",
    "was", "were", "are", "is", "will", "would", "could", "should", "about",
    "into", "after", "before", "their", "there", "them", "they", "said", "says",
    "news", "report", "reports", "reported", "over", "under", "more", "less",
    "than", "amid", "during", "across", "through", "against", "onto", "also",
    "still", "just", "being", "been", "while", "where", "when", "what", "which",
    "who", "whom", "whose", "why", "how", "can", "may", "might", "must", "shall",
    "to", "of", "in", "on", "at", "by", "as", "or", "an", "a", "it", "its",
    "he", "she", "his", "her", "hers", "him", "you", "your", "yours", "we",
    "our", "ours", "they", "them", "i", "me", "my", "mine", "us"
}

VOWEL_ONLY = {"a", "e", "i", "o", "u"}

def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize_prominent_title_words(text):
    text = normalize_text(text)
    tokens = []

    for word in text.split():
        if len(word) < 3:
            continue
        if word in STOP_WORDS:
            continue
        if word in VOWEL_ONLY:
            continue
        if word.isdigit():
            continue
        tokens.append(word)

    return tokens


def get_title_tokens(article):
    title = article.get("title", "") or ""
    return set(tokenize_prominent_title_words(title))


def common_title_keywords(article1, article2):
    t1 = get_title_tokens(article1)
    t2 = get_title_tokens(article2)

    if not t1 or not t2:
        return set()

    return t1.intersection(t2)


def are_same_event(article1, article2, min_common_keywords=5):
    common_keywords = common_title_keywords(article1, article2)

    if len(common_keywords) < min_common_keywords:
        return False

    return True


def group_similar_articles(articles, min_common_keywords=3):
    if not articles:
        return []

    groups = []
    visited = set()

    for i in range(len(articles)):
        if i in visited:
            continue

        current_group = [i]
        visited.add(i)

        for j in range(i + 1, len(articles)):
            if j in visited:
                continue

            if are_same_event(articles[i], articles[j], min_common_keywords=min_common_keywords):
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


def filter_groups_with_min_sources(grouped_articles, min_sources=2, min_articles=2):
    filtered = []

    for group in grouped_articles:
        unique_sources = {
            article.get("source", "").strip().lower()
            for article in group
            if article.get("source", "").strip()
        }

        if len(group) < min_articles:
            continue

        if len(unique_sources) < min_sources:
            continue

        filtered.append(group)

    return filtered


def article_relevance_to_group(article, group):
    if not group:
        return 0.0

    score = 0.0

    for other in group:
        if article.get("url") == other.get("url"):
            continue

        common_keywords = common_title_keywords(article, other)
        score += len(common_keywords)

    return score


def select_top_relevant_articles(group, max_articles=3):
    if not group:
        return []

    scored_group = []

    for article in group:
        article_copy = article.copy()
        article_copy["_relevance_score"] = article_relevance_to_group(article, group)
        scored_group.append(article_copy)

    scored_group.sort(
        key=lambda x: (
            x.get("_relevance_score", 0.0),
            x.get("published_at", "")
        ),
        reverse=True
    )

    trimmed = scored_group[:max_articles]

    for article in trimmed:
        article.pop("_relevance_score", None)

    return trimmed
# ======================================================
# SCORING
# ======================================================
def score_articles_with_both_models(articles):
    scored = []

    for article in articles:
        text = article.get("combined_text", "").strip()
        if not text:
            continue

        article_copy = article.copy()

        try:
            distilbert_result = predict_distilbert(text)
        except Exception as ex:
            print(f"DistilBERT failed for {article.get('url')}: {ex}")
            distilbert_result = {
                "label": "Unknown",
                "confidence": 0.0,
                "raw_score": 0.0,
                "cleaned_text": "",
                "color": "gray"
            }

        try:
            lstm_result = predict_lstm(text)
        except Exception as ex:
            print(f"LSTM failed for {article.get('url')}: {ex}")
            lstm_result = {
                "label": "Unknown",
                "confidence": 0.0,
                "raw_score": 0.0,
                "cleaned_text": ""
            }

        article_copy["distilbert"] = distilbert_result
        article_copy["lstm"] = lstm_result

        scored.append(article_copy)

    return scored


def summarize_group(group):
    if not group:
        return {}

    distilbert_real = sum(1 for a in group if a.get("distilbert", {}).get("label") == "REAL")
    distilbert_fake = sum(1 for a in group if a.get("distilbert", {}).get("label") == "FAKE")

    lstm_real = sum(1 for a in group if a.get("lstm", {}).get("label") == "REAL")
    lstm_fake = sum(1 for a in group if a.get("lstm", {}).get("label") == "FAKE")

    avg_distilbert_conf = round(
        sum(a.get("distilbert", {}).get("confidence", 0.0) for a in group) / max(len(group), 1), 2
    )
    avg_lstm_conf = round(
        sum(a.get("lstm", {}).get("confidence", 0.0) for a in group) / max(len(group), 1), 2
    )

    return {
        "article_count": len(group),
        "sources": list({
            a.get("source", "").strip()
            for a in group
            if a.get("source", "").strip()
        }),
        "distilbert_summary": {
            "real_count": distilbert_real,
            "fake_count": distilbert_fake,
            "avg_confidence": avg_distilbert_conf
        },
        "lstm_summary": {
            "real_count": lstm_real,
            "fake_count": lstm_fake,
            "avg_confidence": avg_lstm_conf
        }
    }


# ======================================================
# PIPELINE
# ======================================================
def build_scored_groups(domain="general", min_sources=2):
    articles = get_all_articles(domain)
    
    print("Raw fetched articles:", len(articles))
    processed = preprocess_articles(articles)
    grouped = group_similar_articles(processed)
    grouped = filter_groups_with_min_sources(grouped, min_sources=min_sources, min_articles=2)

    final_groups = []

    for group_id, group in enumerate(grouped):
        top_group = select_top_relevant_articles(group, max_articles=3)
        scored_group = score_articles_with_both_models(top_group)
        summary = summarize_group(scored_group)

        final_groups.append({
        "group_id": group_id,
        "summary": summary,
        "articles": scored_group
        })

    return final_groups


# ======================================================
# ROUTES
# ======================================================
@app.route("/")
def home():
    return jsonify({
        "message": "Backend running",
        "routes": [
            "/api/analyze?domain=general",
            "/api/analyze?domain=politics",
            "/api/analyze?domain=finance",
            "/api/analyze?domain=sports",
            "/api/analyze?domain=cinema"
        ]
    })


@app.route("/api/analyze", methods=["GET"])
def analyze_news():
    domain = request.args.get("domain", "general").strip().lower()
    
    min_sources = int(request.args.get("min_sources", 2))

    try:
        groups = build_scored_groups(
        domain=domain,
        min_sources=min_sources
        )

        return jsonify({
            "success": True,
            "domain": domain,
            "group_count": len(groups),
            "groups": groups
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/raw-news", methods=["GET"])
def raw_news():
    domain = request.args.get("domain", "general").strip().lower()

    try:
        articles = get_all_articles(domain)
        return jsonify({
            "success": True,
            "domain": domain,
            "count": len(articles),
            "articles": articles
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    
@app.route("/api/trending-news", methods=["GET"])
def trending_news():
    try:
        articles_trending = get_trending_news()
        return jsonify({
            "success": True,
            "count": len(articles_trending),
            "articles": articles_trending
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)