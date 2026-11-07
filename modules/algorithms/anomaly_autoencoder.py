"""
DETECCIÓN DE ANOMALÍAS // AUTOENCODER NEURONAL & ERROR DE RECONSTRUCCIÓN (MSE)
Arquitectura de cuello de botella: D -> 16 -> 4 -> 16 -> D
"""
import numpy as np
from sklearn.neural_network import MLPRegressor

def detect_anomalies_autoencoder(X_features, percentile_threshold=90, random_state=42):
    """
    Entrena un autoencoder para reconstruir la matriz de entrada.
    Las instancias con mayor MSE (error cuadrático medio) se clasifican como anomalías.
    Retorna (errores_mse, umbral_corte, mascara_anomalia, modelo_ae).
    """
    if hasattr(X_features, "toarray"):
        X_dense = X_features.toarray()
    else:
        X_dense = np.asarray(X_features)

    # Autoencoder con cuello de botella
    ae = MLPRegressor(
        hidden_layer_sizes=(16, 4, 16),
        activation='relu',
        max_iter=250,
        random_state=random_state,
        early_stopping=True
    )
    ae.fit(X_dense, X_dense)

    # Reconstrucción
    X_pred = ae.predict(X_dense)
    mse = np.mean((X_dense - X_pred) ** 2, axis=1)

    # Umbral por percentil
    umbral = float(np.percentile(mse, percentile_threshold))
    es_anomalia = mse > umbral

    return mse, umbral, es_anomalia, ae

