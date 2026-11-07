import os, sys, time
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.stdout.reconfigure(encoding='utf-8')

csv_path = 'proyecto/data/chicago_benchmark/bronze/Crimes_-_2020_to_Present_20250228.csv'
parquet_path = 'proyecto/data/chicago_benchmark/silver/chicago_crimes_curated.parquet'

print(f"Iniciando conversión de Chicago CSV ({csv_path})...")
t0 = time.time()

cols_keep = [
    'ID', 'Date', 'Primary Type', 'Description', 'Location Description',
    'Arrest', 'Domestic', 'District', 'Ward', 'Community Area',
    'Year', 'Latitude', 'Longitude'
]

# Lectura y optimización de tipos
df = pd.read_csv(csv_path, usecols=cols_keep)
n_raw = len(df)
print(f"Leídas {n_raw:,} filas en {time.time() - t0:.2f} s")

# Limpieza básica: coordenadas no nulas
df = df.dropna(subset=['Latitude', 'Longitude', 'District']).copy()
df['District'] = df['District'].astype('int16')
df['Year'] = df['Year'].astype('int16')
df['ID'] = df['ID'].astype('int32')
df['Primary Type'] = df['Primary Type'].astype('category')
df['Arrest'] = df['Arrest'].astype('bool')
df['Domestic'] = df['Domestic'].astype('bool')
df['Latitude'] = df['Latitude'].astype('float32')
df['Longitude'] = df['Longitude'].astype('float32')

print(f"Filas limpias: {len(df):,} (descartadas {n_raw - len(df):,})")

# Exportación a Parquet con compresión Snappy
os.makedirs(os.path.dirname(parquet_path), exist_ok=True)
df.to_parquet(parquet_path, engine='pyarrow', compression='snappy', index=False)

csv_size_mb = os.path.getsize(csv_path) / (1024 * 1024)
parquet_size_mb = os.path.getsize(parquet_path) / (1024 * 1024)

print(f"¡Conversión completada con éxito!")
print(f"CSV Original: {csv_size_mb:.2f} MB")
print(f"Parquet Optimizado: {parquet_size_mb:.2f} MB")
print(f"Reducción: {((1 - parquet_size_mb / csv_size_mb) * 100):.1f}% del espacio en disco")
print(f"Tiempo total: {time.time() - t0:.2f} s")

