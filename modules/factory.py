import os
from flask import Flask
from config import config_by_name

def create_app(config_name='dev'):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    )
    
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Registro de Blueprints
    from modules.routes.dashboard_routes import dashboard_bp
    from modules.routes.kmeans_nlp_routes import kmeans_nlp_bp
    from modules.routes.spatial_density_routes import spatial_density_bp
    from modules.routes.api_routes import api_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(kmeans_nlp_bp)
    app.register_blueprint(spatial_density_bp)
    app.register_blueprint(api_bp)

    return app
