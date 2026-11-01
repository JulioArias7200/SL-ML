from flask import Blueprint, render_template
from modules.services.webgis_service import WebGISService

webgis_bp = Blueprint('webgis_bp', __name__)

@webgis_bp.route('/globo-3d')
def globo_3d():
    metadata = WebGISService.get_metadata()
    return render_template(
        'views/globo_3d.html',
        active_page='globo-3d',
        metadata=metadata
    )

