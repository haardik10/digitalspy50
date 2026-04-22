"""Train script for LSTM model. Usage:
python train.py --data_path data/news_dataset.csv --save_dir backend/saved_models

Expects data CSV with columns: 'title', 'text', 'label' (0 or 1)
"""
import argparse
import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, Bidirectional, LSTM, Dense, Dropout
from tensorflow.keras.callbacks import ModelCheckpoint
from backend.model.utils import save_tokenizer
from backend.model.preprocess import clean_text

parser = argparse.ArgumentParser()
parser.add_argument('--data_path', type=str, required=True)
parser.add_argument('--save_dir', type=str, required=True)
parser.add_argument('--max_words', type=int, default=5000)
parser.add_argument('--max_len', type=int, default=300)
parser.add_argument('--embed_dim', type=int, default=128)
args = parser.parse_args()

os.makedirs(args.save_dir, exist_ok=True)

print('Loading data...')
df = pd.read_csv(args.data_path)
df = df.dropna(subset=['text', 'label'])

print('Cleaning texts...')
df['clean_text'] = df['text'].apply(clean_text)

texts = df['clean_text'].tolist()
labels = df['label'].astype(int).tolist()

print('Tokenizing...')
tokenizer = Tokenizer(num_words=args.max_words)
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)
X = pad_sequences(sequences, maxlen=args.max_len)

y = np.array(labels)

X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)

print('Building model...')
model = Sequential()
model.add(Embedding(input_dim=args.max_words, output_dim=args.embed_dim, input_length=args.max_len))
model.add(Bidirectional(LSTM(128, dropout=0.3, recurrent_dropout=0.3, input_shape=(args.max_len,))))
model.add(Dropout(0.5))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.4))
model.add(Dense(1, activation='sigmoid'))


model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
model.summary()

checkpoint_path = os.path.join(args.save_dir, 'lstm_model.h5')
checkpoint = ModelCheckpoint(checkpoint_path, monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')

print('Training...')
model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=6, batch_size=64, callbacks=[checkpoint])

print('Saving tokenizer...')
tokenizer_path = os.path.join(args.save_dir, 'tokenizer.pkl')
save_tokenizer(tokenizer, tokenizer_path)
print('Done. Model saved to', checkpoint_path)
