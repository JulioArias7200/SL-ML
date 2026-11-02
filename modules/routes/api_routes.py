from flask import Blueprint, request, jsonify
from modules.services.kmeans_nlp_service import KMeansNLPService
from modules.services.spatial_service import SpatialDensityService
from modules.services.data_service import DataService
from modules.services.webgis_service import WebGISService
from modules.services.reduction_service import ReductionService
from modules.services.bolivia_service import BoliviaService
from modules.services.chicago_service import ChicagoService

api_bp = Blueprint('api_bp', __name__, url_prefix='/api/v1')

@api_bp.route('/reduction/data', methods=['GET'])
def reduction_data():
    algo = request.args.get('algo', 'pca').lower()
    data = ReductionService.get_algorithm_data(algo)
    return jsonify(data)

@api_bp.route('/bolivia/topics', methods=['GET'])
def bolivia_topics():
    return jsonify(BoliviaService.LDA_TOPICS)

@api_bp.route('/bolivia/anomalies', methods=['GET'])
def bolivia_anomalies():
    return jsonify(BoliviaService.get_anomalies_analysis())

@api_bp.route('/chicago/gmm_predict', methods=['POST'])
@api_bp.route('/gmm_predict', methods=['POST'])
def chicago_gmm_predict():
    data = request.get_json() or {}
    ctx = data.get('ctx', request.args.get('ctx', 'chicago')).lower()
    default_lat = -17.7833 if ctx == 'bolivia' else 41.8781
    default_lon = -63.1821 if ctx == 'bolivia' else -87.6298

    try:
        lat = float(data.get('lat', default_lat))
        lon = float(data.get('lon', default_lon))
    except (ValueError, TypeError):
        return jsonify({"error": "Parámetros lat/lon inválidos"}), 400

    if ctx == 'bolivia':
        res = BoliviaService.simulate_gmm_risk(lat, lon)
    else:
        res = ChicagoService.simulate_gmm_risk(lat, lon)

    return jsonify(res)

@api_bp.route('/webgis/geojson', methods=['GET'])
def webgis_geojson():
    ctx = request.args.get('ctx', 'bolivia').lower()
    bbox = request.args.get('bbox')
    categoria = request.args.get('categoria')
    ciudad = request.args.get('ciudad')
    geojson_data = WebGISService.get_geojson(bbox=bbox, categoria=categoria, ciudad=ciudad, ctx=ctx)
    return jsonify(geojson_data)

@api_bp.route('/webgis/metadata', methods=['GET'])
def webgis_metadata():
    ctx = request.args.get('ctx', 'bolivia').lower()
    metadata = WebGISService.get_metadata(ctx=ctx)
    return jsonify(metadata)

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
    ctx = request.args.get('ctx', 'bolivia').lower()
    try:
        eps = int(request.args.get('eps', 300))
        min_pts = int(request.args.get('min_pts', 25))
    except ValueError:
        return jsonify({"error": "Parámetros numéricos inválidos"}), 400
        
    hud_data = SpatialDensityService.calculate_haversine_hud(eps_meters=eps, min_pts=min_pts, ctx=ctx)
    return jsonify(hud_data)

@api_bp.route('/optics_data', methods=['GET'])
def optics_data():
    ctx = request.args.get('ctx', 'bolivia').lower()
    try:
        xi = float(request.args.get('xi', 0.05))
        min_pts = int(request.args.get('min_pts', 5))
    except ValueError:
        return jsonify({"error": "Parámetros numéricos inválidos"}), 400
    method = request.args.get('method', 'xi').lower()
    
    data = SpatialDensityService.get_optics_data(ctx=ctx, xi=xi, min_pts=min_pts, extraction_method=method)
    return jsonify(data)

@api_bp.route('/telemetry', methods=['GET'])
def telemetry():
    data = DataService.get_dashboard_summary()["hardware_telemetry"]
    return jsonify(data)

@api_bp.route('/districts', methods=['GET'])
def districts():
    ctx = request.args.get('ctx', 'bolivia').lower()
    return jsonify(SpatialDensityService.get_zones(ctx=ctx))
