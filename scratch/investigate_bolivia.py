import math
import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score

df = pd.read_csv('data/web_scraping_news/dashboard_eventos_clusters_bolivia.csv')

def haversine_dist(lat1, lon1, lat2, lon2):
    r = 6371008.8  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * r * math.asin(math.sqrt(a))

print("="*80)
print("PUNTO 3: EL CASO DE ORURO (FILA 48)")
print("="*80)
row48 = df.iloc[48]
print(f"Fila 48: {row48['ciudad']} | {row48['zona_principal']} | Lat: {row48['lat']}, Lon: {row48['lon']}")
print(f"Etiquetas en CSV -> DBSCAN: {row48['dbscan']}, HDBSCAN: {row48['hdbscan']}, OPTICS: {row48['optics']}")

c3_rows = df[df['hdbscan'] == row48['hdbscan']]
print(f"\nClúster HDBSCAN #{row48['hdbscan']} contiene {len(c3_rows)} eventos:")
for idx, r in c3_rows.iterrows():
    dist = haversine_dist(row48['lat'], row48['lon'], r['lat'], r['lon'])
    print(f"  Fila {idx:>2}: {r['ciudad']:<12} | {r['zona_principal']:<15} | ({r['lat']:.4f}, {r['lon']:.4f}) | Dist a Fila 48: {dist/1000:.2f} km")

# Centroid of cluster 3 (excluding row 48)
other_c3 = c3_rows.drop(48)
centroid_lat = other_c3['lat'].mean()
centroid_lon = other_c3['lon'].mean()
dist_centroid = haversine_dist(row48['lat'], row48['lon'], centroid_lat, centroid_lon)
print(f"\n(a) Distancia Haversine al centroide de Cochabamba (Clúster 3): {dist_centroid/1000:.2f} km ({dist_centroid:.1f} m)")
min_dist_neighbor = other_c3.apply(lambda r: haversine_dist(row48['lat'], row48['lon'], r['lat'], r['lon']), axis=1).min()
print(f"(b) Distancia Haversine al vecino más cercano en Clúster 3: {min_dist_neighbor/1000:.2f} km ({min_dist_neighbor:.1f} m)")
print(f"Comparación con ε calibrado (1500 m = 1.5 km): ¡La distancia es {min_dist_neighbor/1500:.1f} veces superior a ε!")

print("\n" + "="*80)
print("PUNTO 4: COORDENADAS DUPLICADAS EN BOLIVIA")
print("="*80)
total_pts = len(df)
coords_df = df[['lat', 'lon']].copy()
unique_coords = coords_df.drop_duplicates()
n_unique = len(unique_coords)
n_duplicated_rows = coords_df.duplicated(keep=False).sum()

print(f"Total eventos georreferenciados: {total_pts}")
print(f"Coordenadas únicas: {n_unique}")
print(f"Eventos con coordenadas idénticas a otro evento: {n_duplicated_rows} ({n_duplicated_rows/total_pts*100:.1f}%)")

counts = coords_df.value_counts()
print("\nTop coordenadas repetidas (posibles centroides de ciudad/macro-zona):")
for (lat, lon), cnt in counts.head(10).items():
    sample_cities = df[(df['lat'] == lat) & (df['lon'] == lon)]['ciudad'].unique().tolist()
    sample_zonas = df[(df['lat'] == lat) & (df['lon'] == lon)]['zona_principal'].unique().tolist()
    print(f"  ({lat:.4f}, {lon:.4f}): {cnt} eventos | Ciudad: {sample_cities} | Zonas: {sample_zonas[:3]}")

# (a) Dependencia de clústeres DBSCAN / HDBSCAN de puntos duplicados
print("\n(a) Dependencia de clústeres en puntos duplicados:")
for model_col in ['dbscan', 'hdbscan']:
    print(f"\nModelo {model_col.upper()}:")
    for c_id, group in df.groupby(model_col):
        n_c = len(group)
        n_unique_c = len(group[['lat', 'lon']].drop_duplicates())
        pct_dup = (n_c - n_unique_c) / n_c * 100
        print(f"  Clúster {c_id:>2}: {n_c:>2} pts | {n_unique_c:>2} coords únicas | Dependencia de duplicados: {pct_dup:.1f}%")

# (b) Silhouette y concentración con vs sin deduplicación
coords_rad = np.radians(df[['lat', 'lon']].to_numpy())
db_mask = df['dbscan'] != -1
sil_db_all = silhouette_score(coords_rad[db_mask], df['dbscan'][db_mask], metric='haversine')

# Deduplicated coordinates: keep one per unique lat/lon
df_dedup = df.drop_duplicates(subset=['lat', 'lon']).copy()
coords_rad_dedup = np.radians(df_dedup[['lat', 'lon']].to_numpy())
db_mask_dedup = df_dedup['dbscan'] != -1
if len(set(df_dedup['dbscan'][db_mask_dedup])) > 1 and db_mask_dedup.sum() > 2:
    sil_db_dedup = silhouette_score(coords_rad_dedup[db_mask_dedup], df_dedup['dbscan'][db_mask_dedup], metric='haversine')
else:
    sil_db_dedup = None

print(f"\n(b) Métricas comparativas con vs sin duplicados:")
print(f"  DBSCAN Silhouette (todos los 60 puntos, 51 asignados): {sil_db_all:.3f}")
print(f"  DBSCAN Silhouette (deduplicado, {len(df_dedup)} puntos únicos, {db_mask_dedup.sum()} asignados): {sil_db_dedup}")

