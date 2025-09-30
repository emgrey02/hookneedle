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

def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.secret_key = os.environ.get('FLASK_SECRET_KEY')
    
    # initialize our app
    from . import db

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
