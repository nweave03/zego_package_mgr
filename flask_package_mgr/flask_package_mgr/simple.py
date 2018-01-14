import os
from flask import Flask, g
from werkzeug.utils import find_modules, import_string
from database import init_db

def register_blueprints(app):
    """
    Register all blueprint modules
    """

    for name in find_modules('flask_package_mgr.blueprints'):
        mod = import_string(name)
        if hasattr(mod, 'bp'):
            app.register_blueprint(mod.bp)

    return None


def register_cli(app):
    @app.cli.command('initdb')
    def initdb_command():
        """
        Creates database tables
        """
        init_db()
        print('Initialized the database.')

def register_teardowns(app):
    @app.teardown_appcontext
    def close_db(error):
        """
        Closes the database again at the end of the request.
        """
        if hasattr(g, 'sqlite_db'):
            g.sqlite_db.close()

app = Flask('flask_package_mgr')

app.config.update(
    dict(
        DATABASE=os.path.join(app.root_path, 'package_mgr.db'),
        DEBUG=True,
        SECRET_KEY='TempKey',
        USERNAME='admin',
        PASSWORD='default'
        )
    )

app.config.from_envvar('FLASK_PACKAGE_MGR_SETTINGS', silent=True)
    
register_blueprints(app)
register_cli(app)
register_teardowns(app)


