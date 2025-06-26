import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def create_app(test_config=None):
    """Application factory function."""
    app = Flask(__name__)
    
    # Configure the app
    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_mapping(
            SECRET_KEY=os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production"),
            SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///app.db'),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
    else:
        # Load the test config if passed in
        app.config.update(test_config)
    
    # Apply proxy fix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    from models import db
    db.init_app(app)
    
    # Initialize Flask-Migrate
    from flask_migrate import Migrate
    migrate = Migrate(app, db)
    
    # Register blueprints
    from routes import discovery_bp, main_bp
    app.register_blueprint(discovery_bp)
    app.register_blueprint(main_bp, url_prefix='')
    
    # Import routes module to register all routes
    import routes
    
    return app

# Create the app instance for backward compatibility
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
