# Dating Scripts — Master Thesis Pipeline

Extracts and analyzes "dating scripts" from Reddit discourse using BERTopic and LLMs.

**Subreddits**: r/dating_advice, r/dating, r/datingoverthirty, r/datingoverforty, r/datingoverfifty, r/OnlineDating, r/AskMen, r/AskWomen

## Pipeline (run in order)

| # | Notebook | What it does |
|---|----------|--------------|
| 1 | `00-fetch_submissions.ipynb` | Downloads full post data via Arctic Shift API in batches of 500 → `pickles/fetched_submissions.pkl` |
| 2 | `01-normalize_fetched_submissions.ipynb` | Normalizes fetched data to pipeline format → `pickles/first-date_posts-all.pkl` |
| 3 | `10-topic_modelling.ipynb` | Embeds posts, runs BERTopic (UMAP → HDBSCAN) → `../pickles/`, `../BERTopic/` |
| 4 | `20-llm_labeling.ipynb` | LLM-based topic labeling |
| 5 | `30-llm_narrative_discovery (Step 1).ipynb` | Discovers narrative patterns via LLM |
| 6 | `40-expansion (Step2).ipynb` | Expands narratives |
| 7 | `50-emotions_analysis (Step3).ipynb` | Emotion classification |
| 8 | `60-explore_results.ipynb` | Explore & inspect results |
| — | `99-visualizations_stats.ipynb` | Publication-ready figures |

## Directory Layout

```
master-thesis-dating-scripts/   ← this repo
../pickles/                     ← cached DataFrames between steps
../embeddings/                  ← sentence embeddings
../BERTopic/                    ← saved BERTopic models
```

## Running

```bash
jupyter lab
```

Run notebooks top-to-bottom. Intermediate results are pickled — re-run only from the step that changed.

**Key deps**: `pandas`, `bertopic`, `sentence-transformers`, `umap-learn`, `hdbscan`, `redditcleaner`, `matplotlib`, `seaborn`
