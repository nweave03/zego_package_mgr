import sqlite3
from flask import g, current_app

from flask_package_mgr import get_db

from error_handlers import IntegrityError, UnhandledError

def query_db(query, args=(), one=False):
    """
    Standard query function that will combine getting the cursor, executing, and
    fetching the results
    """
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    
    print "result {rv}".format(rv=rv)

    if not rv:
        return None

    if one:
        return rv[0]

    return rv

def insert_db(table, fields=(), values=()):
    """
    Used for inserting into the database
    """

    cur = get_db().cursor()
    query = 'INSERT INTO %s (%s) VALUES (%s)' % (
        table,
        ', '.join(fields),
        ', '.join(['?'] * len(values))
        )
    cur.execute(query, values)
    get_db().commit()
    insert_id = cur.lastrowid
    cur.close()
    return insert_id

def table_list(table):
    """
    Used to generate a table list
    """
    return query_db('SELECT * FROM {t}'.format(t=table))

def add_user(username, password, key):
    """
    adds a user to the database
    """
    print "Adding new user {u}, password {p}, apikey {k}".format(
        u=username,
        p=password,
        k=key
        )
    try:
        add_query = insert_db(
                        'users',
                        ['username', 'password', 'apikey'],
                        [username, password, key]
                        )
    except sqlite3.IntegrityError as err:
        raise IntegrityError(message='username is already in use')
    except Exception as err:
        print "Unable to add user {u}, password {p}, apikey {k} because {e}({et})".format(
            u = username,
            p = password,
            k = key,
            e = err,
            et=type(err)
            )
        raise UnhandledError()

def list_users():
    """
    lists users of the database, for testing only
    """
    return table_list('users')
