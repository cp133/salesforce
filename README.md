# 🔍 Generic Duplicate Detection App

This Streamlit-based app allows you to detect and manually review duplicate entries in any CSV dataset using:

- ✅ Exact Match
- 🔁 Fuzzy Match (TF-IDF + Cosine Similarity)
- 🧑 Manual review interface

## 💡 Features

- Upload any CSV
- Choose which columns to match on
- Match using exact or fuzzy logic
- Manual review for each pair
- Final clean output file + change log

## 🛠 How to Run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
