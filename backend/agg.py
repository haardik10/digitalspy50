import pandas as pd

# Load both datasets
true_df = pd.read_csv("data/True.csv")
fake_df = pd.read_csv("data/Fake.csv")

# Add labels
true_df['label'] = 1  # Real news
fake_df['label'] = 0  # Fake news

# Combine them
news_df = pd.concat([true_df, fake_df], axis=0)

# Shuffle for randomness
news_df = news_df.sample(frac=1).reset_index(drop=True)

# Select only necessary columns
news_df = news_df[['title', 'text', 'label']]

# Save combined file
news_df.to_csv("data/news_dataset.csv", index=False)

print("✅ Combined dataset saved as data/news_dataset.csv")
print(news_df.head())
