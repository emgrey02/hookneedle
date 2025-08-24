"""A crochet/knitting project management website"""
__version__ = '0.1'

import os
from flask import Flask, jsonify, render_template

def page_not_found(e):
    er = jsonify(str(e))
    return render_template('404.html', error = er), 404

def internal_server_error(e):
    er = jsonify(str(e))
    return render_template('500.html', error = er), 500

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'hookneedle.db')
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # initialize our app
    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import dash
    app.register_blueprint(dash.bp)
    app.add_url_rule('/', endpoint='index')

    from . import user
    app.register_blueprint(user.bp)

    from. import project
    app.register_blueprint(project.bp)

    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)
    
    return app
