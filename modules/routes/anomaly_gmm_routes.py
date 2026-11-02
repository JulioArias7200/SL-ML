from flask import Blueprint, render_template, request, jsonify
from modules.services.bolivia_service import BoliviaService
from modules.services.chicago_service import ChicagoService

anomaly_gmm_bp = Blueprint('anomaly_gmm_bp', __name__)

@anomaly_gmm_bp.route('/anomalias-probabilistico')
def view():
    anomalies_data = BoliviaService.get_anomalies_analysis()
    return render_template(
        'views/anomalias_autoencoder_gmm.html',
        active_page='anomalias-probabilistico',
        anomalies_data=anomalies_data
    )

@anomaly_gmm_bp.route('/api/gmm_simulate', methods=['POST'])
def gmm_simulate():
    data = request.get_json() or {}
    try:
        lat = float(data.get('lat', 41.8781))
        lon = float(data.get('lon', -87.6298))
    except ValueError:
        return jsonify({"error": "Coordenadas numéricas requeridas"}), 400

    result = ChicagoService.simulate_gmm_risk(lat, lon)
    return jsonify(result)

