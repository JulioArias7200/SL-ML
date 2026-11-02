from flask import Blueprint, render_template, request
from modules.services.kmeans_nlp_service import KMeansNLPService
from modules.services.data_service import DataService

kmeans_nlp_bp = Blueprint('kmeans_nlp_bp', __name__)

@kmeans_nlp_bp.route('/kmeans-nlp')
def view():
    ctx = request.args.get('ctx', 'bolivia').lower()
    if ctx not in ['bolivia', 'chicago']:
        ctx = 'bolivia'

    telemetry = DataService.get_dashboard_summary()["hardware_telemetry"]
    k_metrics = KMeansNLPService.K_METRICS
    archetypes = KMeansNLPService.ARCHETYPES

    return render_template(
        'views/kmeans_nlp.html',
        telemetry=telemetry,
        k_metrics=k_metrics,
        archetypes=archetypes,
        current_context=ctx,
        active_page='kmeans-nlp'
    )
