from flask import Blueprint, request, jsonify
from modules.services.kmeans_nlp_service import KMeansNLPService
from modules.services.spatial_service import SpatialDensityService
from modules.services.data_service import DataService

api_bp = Blueprint('api_bp', __name__, url_prefix='/api/v1')

@api_bp.route('/predict_nlp', methods=['POST'])
def predict_nlp():
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    if not text:
        return jsonify({"success": False, "error": "El texto del reporte no puede estar vacío."}), 400
    
    result = KMeansNLPService.predict_nlp(text)
    return jsonify(result)

@api_bp.route('/spatial_filter', methods=['GET'])
def spatial_filter():
    try:
        eps = int(request.args.get('eps', 300))
        min_pts = int(request.args.get('min_pts', 25))
    except ValueError:
        return jsonify({"error": "Parámetros numéricos inválidos"}), 400
        
    hud_data = SpatialDensityService.calculate_haversine_hud(eps_meters=eps, min_pts=min_pts)
    return jsonify(hud_data)

@api_bp.route('/telemetry', methods=['GET'])
def telemetry():
    data = DataService.get_dashboard_summary()["hardware_telemetry"]
    return jsonify(data)

@api_bp.route('/districts', methods=['GET'])
def districts():
    return jsonify(SpatialDensityService.DISTRICTS)
