from flask import Blueprint, render_template
from modules.services.data_service import DataService

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
def index():
    summary = DataService.get_dashboard_summary()
    return render_template('views/dashboard.html', summary=summary, active_page='dashboard')
