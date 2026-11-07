# CPD ANALYTICS CORE // ARQUITECTURA DE DATOS & PIPELINES (DATA LAKEHOUSE)

Bienvenido a la estructura centralizada de almacenamiento de datos y modelos del proyecto. Esta arquitectura sigue la metodología **Medallion Architecture (Bronze / Silver / Gold)** y separa nítidamente los dominios de análisis.

---

## 1. Estructura de Directorios

```text
proyecto/data/
├── bolivia_news/                              # Dominio Principal: Prensa y Seguridad en Bolivia
│   ├── bronze/                                # Datos crudos e inmutables
│   │   ├── cache_http.sqlite                  # Caché HTTP persistente de requests_cache (23.3 MB)
│   │   └── eventos_bolivia_raw.csv            # Extracción bruta de noticias
│   ├── silver/                                # Datos limpios, normalizados y deduplicados
│   │   ├── eventos_bolivia_cleaned.csv        # Corpus depurado con similitud de cosenos TF-IDF
│   │   └── eventos_bolivia_curated_v5.csv     # Extracción con ámbitos y departamentos
│   └── gold/                                  # Capa de consumo directo para la Web y Modelos
│       ├── spatial_clusters_bolivia.csv       # Coordenadas + DBSCAN / HDBSCAN / OPTICS
│       ├── nlp_topics_anomalies_bolivia.csv   # Tópicos LDA + Error Autoencoder + Flag Anomalía
│       ├── reduction_embeddings.json          # Proyecciones 2D (PCA, SVD, PPCA, t-SNE, UMAP)
│       ├── urban_profiles_bolivia.csv         # Perfiles agregados por zona (K-Means y Ward)
│       └── archive/                           # Histórico de versiones previas (v5, v6...)
│
├── chicago_benchmark/                         # Dominio Secundario: Benchmark de Datos Masivos
│   ├── bronze/                                # CSV original de 1.2M filas (309 MB)
│   │   └── Crimes_-_2020_to_Present_20250228.csv
│   └── silver/                                # Formato columnar Parquet optimizado (20.7 MB, -93.3%)
│       └── chicago_crimes_curated.parquet
│
├── spatial_gazetteers/                        # Diccionarios de barrios OpenStreetMap (OSM)
│   ├── oruro_neighbourhoods.json
│   ├── potosi_neighbourhoods.json
│   ├── sucre_neighbourhoods.json
│   └── tarija_neighbourhoods.json
│
└── notebooks_pipeline/                        # Pipelines interactivos de extracción y ML
    ├── 01_scraping_unsupervised_v5.ipynb
    └── 02_scraping_and_ingestion_v6.ipynb
```

---

## 2. ¿QUÉ SUCEDE Y CÓMO PROCEDER SI HAY UNA NUEVA VERSIÓN DE DATOS?

En esta arquitectura profesional, **nunca se crean carpetas anidadas redundantes** (como `v6/v6`). El ciclo de vida de una nueva versión (ej. `v7` o nueva corrida mensual) sigue un proceso estándar en 4 pasos:

### Paso 1: Ingesta en Capa Bronze (Raw)
- La nueva extracción (scraping) guarda sus respuestas en `bolivia_news/bronze/cache_http.sqlite` y el nuevo CSV bruto se guarda en `bolivia_news/bronze/` con su fecha de corte (ej. `eventos_bolivia_raw_202612.csv`).

### Paso 2: Limpieza en Capa Silver (Cleaned)
- Se ejecuta la deduplicación por similitud de cosenos y normalización geográfica (utilizando los diccionarios de `spatial_gazetteers/`).
- El resultado limpio se publica en `bolivia_news/silver/eventos_bolivia_cleaned.csv`.

### Paso 3: Archivado de la Versión Anterior (Lineage & Rollback)
- Antes de sobrescribir la versión en producción, los archivos actuales de `bolivia_news/gold/` se respaldan en `bolivia_news/gold/archive/v6_20261101/`. Esto garantiza trazabilidad histórica y posibilidad de marcha atrás (*rollback*) inmediata.

### Paso 4: Promoción a Capa Gold (Cero Tiempo de Inactividad)
- Se ejecutan los algoritmos no supervisados sobre el nuevo dataset limpio:
  ```python
  from modules.algorithms import run_spatial_density, compute_embeddings_2d, train_lda_topics, detect_anomalies_autoencoder
  ```
- Los archivos canónicos en `bolivia_news/gold/` se actualizan:
  - `spatial_clusters_bolivia.csv`
  - `nlp_topics_anomalies_bolivia.csv`
  - `reduction_embeddings.json`
- **Ventaja clave:** El servidor Flask, las APIs REST y el visor WebGIS 3D **no necesitan modificar ninguna línea de código**, ya que siempre consumen la versión activa de la capa Gold. El dashboard se actualiza automáticamente con los nuevos datos al recargar la página.

