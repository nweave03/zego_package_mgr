import os
from werkzeug.utils import secure_filename
from package_database import lookup_package_id, store_package_rows, search_all_packages, search_packages, search_all_tags, search_tags
from error_handlers import InvalidUseError, IntegrityError
from flask_package_mgr import app

ALLOWED_EXTENSIONS = set(['txt','npm'])
ALLOWED_EXTENSIONS_TEXT = 'txt, npm'


def search_specific_packages(search_term):
    """
    simple passthrough to search specific packages
    """
    return search_packages(search_term)

def get_all_packages():
    """
    simple passthrough to search all packages
    """
    return search_all_packages()

def allowed_file(filename):
    """
    only allows txt (testing) and npm packages.
    """
    if '.' not in filename:
        raise InvalidUseError('file does not contain \'.\'')
    if filename.rsplit('.',1)[1].lower() not in ALLOWED_EXTENSIONS:
        raise InvalidUseError(
                "file is not of type: {e}".format(
                    e=ALLOWED_EXTENSIONS_TEXT
                    )
                )

def store_file(file, package_name, user, tag):
    """
    This is where file management takes place.  It will place all packages into subfolders based on package name.
    It enforces unique filenames per package.
    """
    if file.filename == '':
        raise InvalidUseError(message='no filename specified')
    if file and allowed_file(file.filename):
        raise InvalidUseError(message='invalid file extension')
    filename = secure_filename(file.filename)
    if '/' in filename:
        raise InvalidUseError(message='filenames cannot contain \'/\'')
    if '/' in tag:
        raise InvalidUseError(message='tags cannot contain \'/\'')
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], package_name)
    if not os.path.exists(filepath):
        os.mkdir(filepath)
    filepath_filename = os.path.join(filepath, filename)
    if os.path.exists(filepath_filename):
        raise IntegrityError(message='filename exists for package')
    file.save(filepath_filename)
    try:
        return store_package_rows(
                package_name=package_name,
                user=user,
                filestore=filepath_filename,
                tag=tag
                )
    except Exception as err:
        # file has to have been saved already from above, so need to catch
        # exceptions and remove the file
        if os.path.exists(filepath_filename):
            os.unlink(filepath_filename)
        raise err

def search_specific_tags(package, tag_search):
    """
    This is a passthrough function to search for specific tags of a package
    """
    return search_tags(
                package_name=package,
                tag_search=tag_search
                )

def get_all_tags(package):
    """
    This function is a passthrough to get all the tags for a package
    """
    return search_all_tags(package_name=package)
