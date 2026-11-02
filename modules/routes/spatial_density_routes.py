from flask import Blueprint, render_template
from modules.services.spatial_service import SpatialDensityService
from modules.services.data_service import DataService

spatial_density_bp = Blueprint('spatial_density_bp', __name__)

@spatial_density_bp.route('/jerarquico-densidad')
@spatial_density_bp.route('/espacial-densidad')
def view():
    telemetry = DataService.get_dashboard_summary()["hardware_telemetry"]
    districts = SpatialDensityService.DISTRICTS
    hud_params = SpatialDensityService.calculate_haversine_hud(eps_meters=300, min_pts=25)
    return render_template(
        'views/espacial_densidad.html',
        telemetry=telemetry,
        districts=districts,
        hud_params=hud_params,
        active_page='espacial-densidad'
    )
