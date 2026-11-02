from flask import Blueprint, render_template, request
from modules.services.webgis_service import WebGISService

webgis_bp = Blueprint('webgis_bp', __name__)

@webgis_bp.route('/globo-3d')
def globo_3d():
    current_context = request.args.get('ctx', 'bolivia').lower()
    if current_context not in ['bolivia', 'chicago']:
        current_context = 'bolivia'
        
    metadata = WebGISService.get_metadata(ctx=current_context)
    return render_template(
        'views/globo_3d.html',
        active_page='globo-3d',
        current_context=current_context,
        metadata=metadata
    )
