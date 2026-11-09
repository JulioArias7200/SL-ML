import json

def inspect_nb(nb_path):
    print("="*80)
    print(f"Inspecting {nb_path}")
    print("="*80)
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    for cell in nb.get('cells', []):
        src = "".join(cell.get('source', []))
        if any(term in src for term in ['hdbscan', 'HDBSCAN', 'optics', 'OPTICS']):
            print("--- CODE CELL ---")
            print(src[:800])
            print("...")

inspect_nb(r'data\notebooks_pipeline\01_scraping_unsupervised_v5.ipynb')

