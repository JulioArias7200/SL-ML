from flask import Blueprint, render_template, request, jsonify
from modules.services.bolivia_service import BoliviaService
from modules.services.chicago_service import ChicagoService

anomaly_gmm_bp = Blueprint('anomaly_gmm_bp', __name__)

@anomaly_gmm_bp.route('/anomalias-probabilistico')
def view():
    ctx = request.args.get('ctx', 'bolivia').lower()
    if ctx != 'chicago':
        ctx = 'bolivia'

    anomalies_data = BoliviaService.get_anomalies_analysis()
    gmm_components = BoliviaService.get_gmm_components() if ctx == 'bolivia' else ChicagoService.get_gmm_components()

    return render_template(
        'views/anomalias_autoencoder_gmm.html',
        active_page='anomalias-probabilistico',
        anomalies_data=anomalies_data,
        gmm_components=gmm_components,
        current_context=ctx
    )

@anomaly_gmm_bp.route('/api/gmm_simulate', methods=['POST'])
def gmm_simulate():
    data = request.get_json() or {}
    ctx = data.get('ctx', request.args.get('ctx', 'bolivia')).lower()
    default_lat = -17.7833 if ctx == 'bolivia' else 41.8781
    default_lon = -63.1821 if ctx == 'bolivia' else -87.6298

    try:
        lat = float(data.get('lat', default_lat))
        lon = float(data.get('lon', default_lon))
    except (ValueError, TypeError):
        return jsonify({"error": "Coordenadas numéricas requeridas"}), 400

    if ctx == 'chicago':
        result = ChicagoService.simulate_gmm_risk(lat, lon)
    else:
        result = BoliviaService.simulate_gmm_risk(lat, lon)

    return jsonify(result)

