import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib

# small example dataset
data = [
    ("Peux-tu résumer ce document ?", "ASK_SUMMARY"),
    ("Où est-ce que je peux acheter X-Phone ?", "ASK_AVAILABILITY"),
    ("Comment comparer X-Phone et Y-Phone ?", "ASK_COMPARE"),
]

df = pd.DataFrame(data, columns=['text', 'intent'])
vec = TfidfVectorizer(max_features=2000)
X = vec.fit_transform(df['text'])
model = LogisticRegression(max_iter=200)
model.fit(X, df['intent'])
joblib.dump(model, './data/intent_model.pkl')
joblib.dump(vec, './data/intent_model.pkl.vec')
print('Saved intent model')
