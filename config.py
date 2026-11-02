import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cpd-analytics-core-secret-key-2026')
    DEBUG = False
    TESTING = False
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = os.path.join(BASE_DIR, 'data')
    STATIC_PATH = os.path.join(BASE_DIR, 'static')
    TEMPLATES_PATH = os.path.join(BASE_DIR, 'templates')

    # =========================================================================
    # ARQUITECTURA MEDALLION & RUTAS CANÓNICAS DE DATOS
    # =========================================================================
    # Dominio 1: Bolivia News (Seguridad Ciudadana & NLP)
    DATA_BOLIVIA_DIR = os.path.join(DATA_PATH, 'bolivia_news')
    DATA_BOLIVIA_BRONZE = os.path.join(DATA_BOLIVIA_DIR, 'bronze')
    DATA_BOLIVIA_SILVER = os.path.join(DATA_BOLIVIA_DIR, 'silver')
    DATA_BOLIVIA_GOLD = os.path.join(DATA_BOLIVIA_DIR, 'gold')

    # Dominio 2: Chicago Benchmark (840k+ registros)
    DATA_CHICAGO_DIR = os.path.join(DATA_PATH, 'chicago_benchmark')
    DATA_CHICAGO_BRONZE = os.path.join(DATA_CHICAGO_DIR, 'bronze')
    DATA_CHICAGO_SILVER = os.path.join(DATA_CHICAGO_DIR, 'silver')
    DATA_CHICAGO_GOLD = os.path.join(DATA_CHICAGO_DIR, 'gold')

    # Diccionarios espaciales y Pipelines
    DATA_GAZETTEERS_DIR = os.path.join(DATA_PATH, 'spatial_gazetteers')
    DATA_PIPELINES_DIR = os.path.join(DATA_PATH, 'notebooks_pipeline')

    # Archivos canónicos para producción (Capa Gold)
    PATH_BOLIVIA_CLUSTERS = os.path.join(DATA_BOLIVIA_GOLD, 'spatial_clusters_bolivia.csv')
    PATH_BOLIVIA_NLP_TOPICS = os.path.join(DATA_BOLIVIA_GOLD, 'nlp_topics_anomalies_bolivia.csv')
    PATH_BOLIVIA_EMBEDDINGS = os.path.join(DATA_BOLIVIA_GOLD, 'reduction_embeddings.json')
    PATH_BOLIVIA_URBAN_PROFILES = os.path.join(DATA_BOLIVIA_GOLD, 'urban_profiles_bolivia.csv')
    PATH_CHICAGO_PARQUET = os.path.join(DATA_CHICAGO_SILVER, 'chicago_crimes_curated.parquet')

    # Ruta de respaldo legacy para compatibilidad
    LEGACY_NEWS_PATH = os.path.join(DATA_PATH, 'web_scraping_news')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
    'default': DevelopmentConfig
}
