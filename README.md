# NewsVeriFy - Flask (HTML templates) - Quick Start

## What this archive contains
A lightweight Flask app that:
- Aggregates news via RSS feeds (newspaper3k)
- Cleans text and runs an LSTM-based classifier (TensorFlow/Keras)
- Serves a simple HTML frontend (Bootstrap) to fetch & show classified articles

## Prerequisites
- Python 3.9+ (3.10 recommended)
- pip (and optionally a virtualenv)

## Install and run (local)
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Prepare dataset (example): place CSV with columns 'title', 'text', 'label' at data/news_dataset.csv
# Train the model:
python backend/model/train.py --data_path data/news_dataset.csv --save_dir backend/saved_models

# Start the app (after training)
python backend/app.py

# Open http://127.0.0.1:5000 in the browser.
```

## Notes
- This project does NOT include pre-trained models or datasets due to size/legal reasons.
- Use small datasets for quick testing, and respect robots.txt when scraping.
