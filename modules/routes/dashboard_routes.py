from flask import Blueprint, render_template, request
from modules.services.bolivia_service import BoliviaService
from modules.services.chicago_service import ChicagoService

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
def index():
    ctx = request.args.get('ctx', 'bolivia').lower()
    if ctx == 'chicago':
        summary = ChicagoService.get_dashboard_summary()
    else:
        ctx = 'bolivia'
        summary = BoliviaService.get_dashboard_summary()
        
    return render_template(
        'views/dashboard.html',
        summary=summary,
        active_page='dashboard',
        current_context=ctx
    )
