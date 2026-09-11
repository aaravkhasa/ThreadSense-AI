THREADSENSE AI — PROJECT FOLDER
================================
Extract this entire ThreadSense-AI folder and open your editor (VS Code /
Jupyter) AT THIS FOLDER — not inside a subfolder. Everything below assumes
that as your working directory.

data/raw/               Original raw dataset (Step 1 output)
data/archive/            Old/backup xlsx files — safe to ignore, kept only
                          for reference (Channel_Summary and
                          Stock_Reallocations sheets live inside
                          JAK_Threads_Master_Dataset.xlsx here)
data/processed/           jak_threads_locked_in_verified.xlsx
                          <-- YOUR ONE WORKING FILE. Everything from here
                          on reads from this file.

src/                     generate_retail_dataset.py  — Step 1 code
                          feature_engineering.py       — Step 3 code

notebooks/                04_risk_classification.ipynb — Step 4, ready to
                          run top to bottom. Open Jupyter/VS Code here.

models/                   Empty until you run the notebook — it will save
                          risk_classifier.pkl here automatically.

dashboard/                Empty — this is where Step 8's Streamlit app.py
                          will go later.

report/                   Your project log and the original build guide —
                          useful when writing the final report.

NEXT STEP
---------
Open notebooks/04_risk_classification.ipynb and run every cell in order.
