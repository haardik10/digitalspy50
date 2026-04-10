from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from backend.distilbert_model import predict_news
import os
from backend.aggregator import get_latest_articles
from backend.model.utils import load_tokenizer
from tensorflow.keras.models import load_model
from backend.model.preprocess import clean_text
from tensorflow.keras.preprocessing.sequence import pad_sequences

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_DIR = os.path.join(BASE_DIR, 'saved_models')

app = Flask( __name__, template_folder=os.path.join(BASE_DIR, '../templates'), static_folder=os.path.join(BASE_DIR, '../static') )
CORS(app)

model = None
tokenizer = None
MAX_LEN = 300

try:
    model_path = os.path.join(SAVED_DIR, 'lstm_model.h5')
    tokenizer_path = os.path.join(SAVED_DIR, 'tokenizer.pkl')

    if os.path.exists(model_path) and os.path.exists(tokenizer_path):
        model = load_model(model_path)
        tokenizer = load_tokenizer(tokenizer_path)
        print('✅ Loaded model and tokenizer from', SAVED_DIR)
    else:
        print('⚠️ Model or tokenizer not found.')
except Exception as e:
    print('❌ Error loading model:', e)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/fetch-and-classify', methods=['GET'])
def fetch_and_classify():
    articles = get_latest_articles()
    results = []

    for a in articles:
        text = a.get('text', '')
        cleaned = clean_text(text)

        if model and tokenizer:
            seq = tokenizer.texts_to_sequences([cleaned])
            pad = pad_sequences(seq, maxlen=MAX_LEN)
            pred = float(model.predict(pad, verbose=0)[0][0])
            label = 'Real' if pred > 0.5 else 'Fake'
        else:
            pred = None
            label = 'Model not trained'

        results.append({
            'title': a.get('title'),
            'url': a.get('url'),
            'source': a.get('source'),
            'prediction': label,
            'confidence': pred
        })

    return jsonify(results)


@app.route('/predict_text', methods=['POST'])
def predict_text():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text:
            return jsonify({'result': 'No input provided', 'confidence': 0}), 400

        result = predict_news(text)

        return jsonify({
            'result': result['prediction'],
            'confidence': result['confidence']
        })
    except Exception as e:
        return jsonify({
            'result': 'Error',
            'confidence': 0,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True)