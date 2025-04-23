import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import DEFAULT_SIMILARITY_THRESHOLD


def exact_match(df, selected_columns):
    df["_match_str"] = df[selected_columns].astype(str).agg(" ".join, axis=1)
    duplicates = df[df.duplicated(subset=["_match_str"], keep=False)].copy()
    return duplicates.drop(columns=["_match_str"])


def fuzzy_match(df, selected_columns, threshold=DEFAULT_SIMILARITY_THRESHOLD):
    df["_match_str"] = df[selected_columns].astype(str).agg(" ".join, axis=1)
    tfidf = TfidfVectorizer().fit_transform(df["_match_str"].fillna(""))
    cosine_sim = cosine_similarity(tfidf)
    matches = []

    for i in range(len(df)):
        for j in range(i + 1, len(df)):
            score = cosine_sim[i, j]
            if score > threshold:
                matches.append(
                    {"Row A Index": i, "Row B Index": j, "Similarity": score}
                )

    return pd.DataFrame(matches)
