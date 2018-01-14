from sqlite3 import dbapi2 as sqlite3
from flask import Blueprint, request, session, g, abort, current_app

# create blueprint
bp = Blueprint('flask_package_mgr', __name__)

def connect_db():
    """
    Connects to the specific database.
    """
    rv = sqlite3.connect(current_app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
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



