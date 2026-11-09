from flask import Blueprint, render_template, request
from modules.services.reduction_service import ReductionService

reduction_bp = Blueprint('reduction_bp', __name__)

@reduction_bp.route('/reduccion-espacios')
def view():
    ctx = request.args.get('ctx', 'bolivia').lower()
    if ctx not in ['bolivia', 'chicago']:
        ctx = 'bolivia'
    algo = request.args.get('algo', 'pca').lower()
    data = ReductionService.get_algorithm_data(algo, ctx=ctx)
    return render_template(
        'views/reduccion_dimensionalidad.html',
        active_page='reduccion-espacios',
        data=data,
        current_algo=algo,
        current_context=ctx
    )

