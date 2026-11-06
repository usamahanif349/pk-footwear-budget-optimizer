"""
What do customers praise and complain about, per brand? (from Project 1)

Reads Project 1's labelled reviews (XLM-R predictions on YouTube comments and
Google Maps reviews) and counts, per brand and aspect, how many mentions were
positive or negative. The aspect keywords (English + Roman Urdu) are the same
ones used in the Project 1 dashboard. The result feeds the "What to say" part of
the marketing plan.

Usage (Command Prompt):  python src\\analysis\\project1_aspects.py
(downloads results_bert.csv from the Project 1 GitHub repo, or pass --file)
"""
import argparse
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed"
P1_FILE = ("https://raw.githubusercontent.com/usamahanif349/pk-footwear-sentiment-analysis/"
           "main/data/processed/results_bert.csv")

ASPECTS = {
    "price": ["price", "prices", "expensive", "costly", "cheap", "mehnga", "mehngi",
              "mehngay", "sasta", "sasti", "qeemat", "value", "paisa", "paise", "discount", "sale"],
    "quality": ["quality", "durable", "durability", "material", "leather", "sole", "stitching",
                "tut", "toot", "tootgaya", "original", "fake"],
    "comfort": ["comfort", "comfortable", "uncomfortable", "soft", "cushion", "pain",
                "aaram", "aram", "walking"],
    "size": ["size", "sizes", "sizing", "fitting", "tight", "loose", "chota", "chhota",
             "bara", "bada"],
    "design": ["design", "designs", "style", "stylish", "look", "looks", "color", "colour",
               "collection", "variety"],
    "staff": ["staff", "salesman", "salesmen", "rude", "helpful", "polite", "behaviour",
              "behavior", "manager", "counter", "cashier"],
    "delivery": ["delivery", "delivered", "courier", "parcel", "shipping", "order", "online"],
}


def aspect_table(d):
    d = d.copy()
    d["clean_text"] = d["clean_text"].fillna("").astype(str)
    rows = []
    for aspect, words in ASPECTS.items():
        pat = re.compile(r"\b(?:" + "|".join(words) + r")\b")
        hit = d[d["clean_text"].apply(lambda t: bool(pat.search(t)))]
        for brand, g in hit.groupby("brand"):
            rows.append(dict(brand=brand, aspect=aspect, mentions=len(g),
                             positive=round((g["bert_pred"] == "positive").mean(), 3),
                             negative=round((g["bert_pred"] == "negative").mean(), 3)))
    t = pd.DataFrame(rows)
    t["net"] = (t["positive"] - t["negative"]).round(3)
    return t.sort_values(["brand", "mentions"], ascending=[True, False])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=P1_FILE, help="Project 1 results_bert.csv (path or URL)")
    args = ap.parse_args()
    t = aspect_table(pd.read_csv(args.file))
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "brand_aspects.csv", index=False)
    print(t.to_string(index=False))
    print(f"\nSaved -> {OUT / 'brand_aspects.csv'}")


if __name__ == "__main__":
    main()
