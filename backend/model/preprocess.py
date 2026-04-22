import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# downloads will run the first time (ensure internet available during training)
nltk.download('stopwords')
try:
    nltk.download('wordnet')
except Exception:
    pass

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ''
    text = re.sub(r'http\\S+', '', text)
    text = re.sub(r'[^a-zA-Z]', ' ', text)
    text = text.lower()
    tokens = [lemmatizer.lemmatize(t) for t in text.split() if t not in stop_words]
    return ' '.join(tokens)

from tensorflow.keras.preprocessing.sequence import pad_sequences

def texts_to_padded_sequences(tokenizer, texts, max_len=300):
    seq = tokenizer.texts_to_sequences(texts)
    return pad_sequences(seq, maxlen=max_len)
