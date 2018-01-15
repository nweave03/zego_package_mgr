import os
from flask import Flask, g, current_app
from werkzeug.utils import find_modules, import_string
from sqlite3 import dbapi2 as sqlite3
import error_handlers

def make_dicts(cursor, row):
    """
    Standard row factory function to make it return dictionaries instead of tuples
    """
    return dict((cursor.description[idx][0], value) for idx, value in enumerate(row))

def connect_db():
    """
    Connects to the specific database.
    """
    rv = sqlite3.connect(current_app.config['DATABASE'])
    rv.row_factory = make_dicts 
    return rv

def init_db():
    """
    Initializes the database.
    """
    db = get_db()
    with current_app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def get_db():
    """
    Opens a new database connection if ther eis none yet for the current application
    context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

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
    
register_cli(app)
register_teardowns(app)

from blueprints.routes import pckg
app.register_blueprint(pckg)


