import json

path = 'data/notebooks_pipeline/01_scraping_unsupervised_v5.ipynb'
with open(path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

cell = nb['cells'][39]
old_src = ''.join(cell['source'])

# Target code to replace
old_export = """# 3. Exportación de resultados para el Dashboard
if ZONAS_OK:
    esp.to_csv("dashboard_eventos_clusters_bolivia.csv", index=False, encoding="utf-8")
    TZ.to_csv("dashboard_zonas_perfiles_bolivia.csv", encoding="utf-8")
dfc.to_csv("dashboard_texto_nlp_bolivia.csv", index=False, encoding="utf-8")
print("Archivos CSV exportados para el dashboard.")"""

new_export = """# 3. Exportación de resultados para el Dashboard
os.makedirs("data/bolivia_news/gold", exist_ok=True)
if ZONAS_OK:
    esp.to_csv("data/bolivia_news/gold/dashboard_eventos_clusters_bolivia.csv", index=False, encoding="utf-8")
    TZ.to_csv("data/bolivia_news/gold/dashboard_zonas_perfiles_bolivia.csv", encoding="utf-8")
dfc.to_csv("data/bolivia_news/gold/dashboard_texto_nlp_bolivia.csv", index=False, encoding="utf-8")
print("Archivos CSV exportados para el dashboard en data/bolivia_news/gold/.")"""

if old_export in old_src:
    new_src = old_src.replace(old_export, new_export)
    # Split into lines keeping line breaks
    cell['source'] = [line + '\n' for line in new_src.splitlines()]
    # fix last line ending if needed
    if not new_src.endswith('\n'):
        cell['source'][-1] = cell['source'][-1].rstrip('\n')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print("Updated cell 39 successfully.")
else:
    print("Old export pattern not found verbatim. Inspecting lines:")
    print(repr(old_src[-300:]))

