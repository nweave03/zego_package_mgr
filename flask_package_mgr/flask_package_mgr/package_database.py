import sqlite3
from flask import g, current_app

from flask_package_mgr import get_db

from error_handlers import IntegrityError, UnhandledError, NotFoundError

def query_db(query, args=(), one=False):
    """
    Standard query function that will combine getting the cursor, executing, and
    fetching the results
    """
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    
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
    return query_db(
            query='SELECT * FROM {t}'.format(t=table)
            )

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
                        table='users',
                        fields=['username', 'password', 'apikey'],
                        values=[username, password, key]
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

def lookup_user_id(username):
    """
    looks up a user id by their username
    """

    try:
        search_query = "SELECT id FROM users WHERE username = ?"
        user_id = query_db(
                    query=search_query,
                    args = [ username ],
                    one=True
                    )
        return user_id['id'] if user_id != None else None
    except Exception as err:
        print "Unable to lookup_user_id username={u} : {e}".format(
                    u=username,
                    e=err
                    )
        raise UnhandledError()

def list_users():
    """
    lists users of the database, for testing only
    """
    return table_list('users')

def lookup_password(user):
    """
    Lookup a users password.  This is not a good way of doing this.  The 
    database is not salted or hashed.  But this is a quick way of doing this.
    """

    try:
        password_query = "SELECT password FROM users WHERE username = ?";
        password = query_db(
                query=password_query,
                args=[ user ]
                )
        if None == password:
            raise IntegrityError(message='username not found')
        return password[0]['password']
    except Exception as err:
        print "Unhandled Error lookup up user {u} : {e}".format(
                    u=user,
                    e=err
                    )
        raise UnhandledError()



def search_all_packages():
    """
    returns a list of all packages currently being stored
    """
    try:
        all_packages_query = "SELECT title, id FROM packages"
        packages = query_db(
                query=all_packages_query
                )
        if None == packages:
            packages = []
        return packages
    except Exception as err:
        print "Unhandled Error in search_all_packages : {e}".format(
                    e=err
                    )
        raise UnhandledError()



def search_packages(search_term):
    """
    Allows users to search for specific text within a package name
    """
    try:
        search_query = "SELECT title, id FROM packages WHERE title LIKE ?"
        search_term = "%{st}%".format(st=search_term)
        packages = query_db(
                query=search_query,
                args=[ search_term ]
                )
        if None == packages:
            packages = []
        return packages
    except Exception as err:
        print "Unhandled Error in search_packages {st} : {e}".format(
                    st=search_term,
                    e=err
                    )
        raise UnhandledError()

def lookup_package_id(package_name):
    """
    looks up the package id for the given package name, if exists
    """
    try:
        search_query = "SELECT id FROM packages WHERE title = ?"
    
        package_id = query_db(
                query=search_query,
                args = [ package_name ],
                one=True
                )

        return package_id['id'] if package_id is not None else None
    except Exception as err:
        print "Unhandled Error in lookup_package_id {pn} : {e}".format(
                    pn = package_name,
                    e=err
                    )

        raise UnhandledError()
 
def store_package_name(package_name, user):
    """
    stores a new package in the database, should only be used after checking lookup_package_id
    """
    try:
        add_package_id = insert_db(
                        table='packages',
                        fields=[ 'title', 'user_id' ],
                        values=[ package_name, user ]
                        )
        return add_package_id
    except sqlite3.IntegrityError as err:
        raise IntegrityError(message='package name already in use')
    except Exception as err:
        print "Unhandled Error in store_package_name package_name={pn} user={u} : {e}".format(
                                pn=package_name,
                                u=user,
                                e=err
                                )
        raise UnhandledError()

def delete_package(package_id):
    """
    removes a package from the database package table, used for cleanup from errors
    """
    try:
        delete_query = "DELETE FROM packages WHERE id = ?"

        query_db(
            query=delete_query,
            args = [ package_id ]
            )
        return True
    except Exception as err:
        print "could not delete package {pd} from table : {e}".format(
                                pd = package_id,
                                e = err
                                )
        raise UnhandledError()


def lookup_filestore_id(filestore):
    """
    looks up a current filestore_id from a package location
    """
    try:
        search_query = "SELECT id FROM filestore WHERE package_filepath = ?"

        filestore_id = query_db(
                query=search_query,
                args = [ filestore ],
                one=True
                )
        return filestore_id['id'] if filestore_id is not None else None
    except Exception as err:
        print "Unhandled Error in lookup_filestore_id filestore={f} : {e}".format(
                        f=filestore,
                        e=err
                        )
        raise UnhandledError()

def store_filestore(filestore):
    """
    stores a new filestore in the database, should only be used after checking lookup_filestore_id
    """
    try:
        add_filestore_id = insert_db(
                    table='filestore',
                    fields = [ 'package_filepath' ],
                    values = [ filestore ]
                    )
        return add_filestore_id
    except sqlite3.IntegrityError as err:
        print "Package location is not unique : {f}".format(
                f=filestore
                )
        raise UnhandledError()
    except Exception as err:
        print "Unhandled Error in store_filename filestore={f} : {e}".format(
                    f=filestore,
                    e=err
                    )
        raise UnhandledError()

def delete_filestore(filestore_id):
    """
    deletes a filestore from the database, used for cleanup from errors
    """
    try:
        delete_query = "DELETE FROM filestore WHERE id = ?"

        query_db(
            query = delete_query,
            args = [ filestore_id ]
            )
        return True
    except Exception as err:
        print "could not delete filestore id {fi} from filestore : {e}".format(
                                fi = filestore_id,
                                e = err
                                )
        raise UnhandledError()

def lookup_tag_id(package_id, tag):
    """
    looks up the tag_id of a package and file location
    """
    try:
        search_query = "SELECT id FROM tags WHERE package_id = ? AND tag = ?"

        tag_id = query_db(
                    query=search_query,
                    args = [ package_id, tag ],
                    one=True
                    )
        return tag_id['id'] if tag_id is not None else None
    except Exception as err:
        print "Unhandled Error lookup_tag_id package_id={pi} tag={t} : {e} {et}".format(
                        pi=package_id,
                        t=tag,
                        e=err,
                        et=type(err)
                        )
        raise UnhandledError()

def store_tag(package_id, filestore_id, tag):
    try:
        add_tag_id = insert_db(
                    table='tags',
                    fields = [ 'tag', 'package_id', 'filestore_id' ],
                    values = [ tag, package_id, filestore_id ]
                    )
        return add_tag_id
    except sqlite3.IntegrityError as err:
        print "Tag and package_id are not unique. package_id={pi} filestore_id={fi} tag={t}: {e}".format(
                            pi=package_id,
                            fi=filestore_id,
                            t=tag,
                            e=err
                            )
        raise IntegrityError(message='Tag is not unique to package')
    except Exception as err:
        print "Unhandled Error in store_tag_id package_id={pi} filestore_id={fi} tag={t} : {e}".format(
                            pi=package_id,
                            fi=filestore_id,
                            t=tag,
                            e=err
                            )
        raise UnhandledError()

def cleanup_add(package_id, filestore_id):
    """
    cleanup for insertion attempts that fail at a later stage
    """
    if None != package_id:
        delete_package(package_id=package_id)
    if None != filestore_id:
        delete_filestore(filestore_id=filestore_id)
    return None

def store_package_rows(package_name, user, filestore, tag):
    """ 
    The complete storing of an entire package
    """

    # this is used to detect if the package already existed before this
    # attempt.  aids in cleanup
    curr_package_id = lookup_package_id(
                        package_name=package_name
                        )
   
    package_id = curr_package_id
    if None == package_id:
        package_id = store_package_name(
                        package_name=package_name,
                        user=user
                        )

    curr_filestore_id = lookup_filestore_id(
                        filestore=filestore
                        )
    print "found filestore id {f}".format(f= curr_filestore_id)
    filestore_id = curr_filestore_id
    if None == filestore_id:
        try:
            filestore_id = store_filestore(
                        filestore=filestore
                        )
        except Exception as err:
            cleanup_add(
                package_id = package_id if (curr_package_id == None) else None,
                filestore_id = None
                )
            raise UnhandledError()
    
    tag_id = lookup_tag_id(
                package_id=package_id,
                tag=tag
                )
    if None != tag_id:
        # this means the tag already exists for adding this package
        cleanup_add(
            package_id = package_id if (curr_package_id == None) else None,
            filestore_id = filestore_id if (curr_filestore_id == None) else None
            )
        raise IntegrityError(message='tag is already in use for package')

    # store the tag in the database
    try:
        tag_id = store_tag(
                package_id=package_id,
                filestore_id=filestore_id,
                tag=tag
                )
    except IntegrityError as err:
        cleanup_add(
            package_id = package_id if (curr_package_id == None) else None,
            filestore_id = filestore_id if (curr_filestore_id == None) else None
            )
        raise err
    except Exception as err:
        cleanup_add(
            package_id = package_id if (curr_package_id == None) else None,
            filestore_id = filestore_id if (curr_filestore_id == None) else None
            )
        raise UnhandledError()
    return { 
            'package_id' : package_id,
            'tag_id' : tag_id
            }


def search_all_tags_by_id(package_id):
    """
    returns a list of all tags for a specific package
    """
    try:
        all_tags_query = "SELECT tag, id FROM tags WHERE package_id = ?"
        tags = query_db(
                query=all_tags_query,
                args = [ package_id ]
                )
        if None == tags:
            tags = []
        return tags
    except Exception as err:
        print "Unhandled Error in search_all_tags_by_id: package_id {pi} : {e}".format(
                    pi=package_id,
                    e=err
                    )
        raise UnhandledError()



def search_tags_by_id_and_term(package_id, tag_search_term):
    """
    Allows users to search for specific text within a packages' tag
    """
    try:
        search_query = "SELECT tag, id FROM tags WHERE package_id = ? AND tag LIKE ?"
        search_term = "%{tst}%".format(tst=tag_search_term)
        tags = query_db(
                query=search_query,
                args=[ package_id, search_term ]
                )
        if None == tags:
            tags = []
        return tags
    except Exception as err:
        print "Unhandled Error in search_tags_by_id_and_term: package_id {pi}, tag_search_term {tst} : {e}".format(
                    pi=package_id,
                    tst=tag_search_term,
                    e=err
                    )
        raise UnhandledError()

def search_all_tags(package_name):
    """
    looks up a package and return all of its tags that are available
    """
    package_id = lookup_package_id(
                        package_name=package_name
                        )
    if package_id == None:
        raise NotFoundError(message='could not locate package')

    return search_all_tags_by_id(package_id=package_id)

def search_tags(package_name, tag_search):
    """
    looks up a package and searches its tag for specific parameters
    """
    package_id = lookup_package_id(
                        package_name=package_name
                        )

    if package_id == None:
        raise NotFoundError(message='could not locate package')

    return search_tags_by_id_and_term(
                package_id = package_id,
                tag_search_term=tag_search
                )


