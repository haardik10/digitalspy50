import pickle

def save_tokenizer(tokenizer, path):
    with open(path, 'wb') as f:
        pickle.dump(tokenizer, f)

def load_tokenizer(path):
    with open(path, 'rb') as f:
        return pickle.load(f)
