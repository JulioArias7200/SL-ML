import json

nb_path = r'data\notebooks_pipeline\01_scraping_unsupervised_v5.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, cell in enumerate(nb.get('cells', [])):
    src = "".join(cell.get('source', []))
    if 'dashboard_eventos_clusters_bolivia.csv' in src:
        print(f"Cell #{i}:")
        print(src)
        print("="*60)

