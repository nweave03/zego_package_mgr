# zego_package_mgr

## Basic Setup
This is designed to used the basic venv that flask recommends.  

> pip install virtualenv

or possibly

> apt-get install python-virtualenv

Then go into the directory flask_package_mgr and activate the virtualenv

>cd flask_package_mgr
>virtualenv venv
>. venv/bin/activate

Then you will need to install Flask, pytest, and the application

>pip install flask
>pip install pytest
>pip install --editable .

Now we want to create the initial blank database

>export FLASK_APP=flask_package_mgr
>flask initdb

## Basic running
The app is not complicated yet.  I have not had time to add an actual configuration file, 
so for now it runs on localhost. If you want to run it on the localhost then do the followin:

>export FLASK_APP=flask_package_mgr
>flask run

## Testing
Right now most of the functionality has been tested with pytest.  If you wish to see the tests run
then run pytest

>pytest

if you wish to see the log outputs run without supressing text

>pytest -s

## API Definitions
The API has a few routes:
* `/api/v1/admin/user_list`
    * content_type - application/json
    * methods - GET
    * json inputs
        * None
    * response codes
        * `200` - Success
        * `500` - Internal Server Error
    * Notes - this is an insecure endpoint only for testing purposes, it would be removed in any actual deployment

* `/api/v1/user/add`
    * content_type - application/json
    * methods - POST
    * json inputs
        * `username` - Required, string/text username of new user
        * `password` - Required, string/text password of new user
    * response codes
        * `200` - Success
        * `400` - Invalid Use did not include above inputs
        * `409` - Conflict - username is already in use
        * `500` - Internal Server Error
    * Notes - this is the endpoint used to add a new user to the system

* `/api/v1/user/get_token`
    * content_type - application/json
    * methods - POST (is a post because it *should* create an entry in a database, at this point could be a GET)
    * json inputs
        * `username` - Required, string/text username of existing user
        * `password` - Required, string/text password of existing user
    * response codes
        * `200` - Success
        * `400` - Invalid Use did not include above inputs
        * `401` - Unauthorized typically password is incorrect
        * `404` - Not Found, typcially username not found
        * `500` - Internal Server Error
    * json response
        * `token` - the authorization token to continue using the api
    * Notes - this is the endpoint to get the token for authorization, right now is a basic check, no salting/hashing or anything

* `/api/v1/user/invalidate_token`
    * content_type - application/json
    * methods - POST
    * headers
        * `token` - token from get_token
    * json inputs
        * `username` - Required, string/text username of token user
        * `password` - Required, string/text password of token user
    * response codes
        * `200` - Success
        * `400` - Invalid Use typically did not include above inputs
        * `401` - Unauthorized typically password is incorrect
        * `404` - Not Found, typically username not found
        * `500` - Internal Server Error
    * json response
        * `message` - message describing revokation
    * Notes - this is mostly a test endpoint, but it could be used to manually invalidate a token rather than wait for a timeout

* `/api/v1/packages`
    * method - POST
        * content_type - multipart/form-data
        * file `json` - (ran into trouble with werkzeug on this, so it has a weird API)
            * `filename` should contain json parameters 
                * `package_name` - Required, string/text package name (cannot contain '/')
                * `tag` - Required, string text tag (cannot contain '/')
            * pass as type `application/json`
            * data is ignored
        * file `file`
            * pass file wanting to upload, could be `application/octet-stream` or `text/plain`
        * headers
            * `token` - token from get_token
        * response codes
            * `200` - Success
            * `400` - Invalid Use typically did not include above inputs or file
            * `401` - Unauthorized typically token is incorrect
            * `409` - Conflict, typically something that needs to be unique is not
            * `500` - Internal Server Error
        * response json (I had the thought of using these id's as an alternate accessor of the API, didn't pursue)
            * `package_id` - id of the package
            * `tag_id` - id of the tag
        * Notes - this is a very crazy API.  I tried to figure out why werkzeug was not allowing me to do this in a
          sane way, but I ran out of time.  I tried a ton of different options, but just settled for getting it working.
    * method - GET
        * content_type - application/json
        * headers
            * `token` - token from get_token
        * json inputs
            * `search` - optional, string/text, if not included will return all packages
        * response codes
            * `200` - Success
            * `401` - Unauthorized typically token is incorrect
            * `500` - Internal Server Error
        * response json
            * list of the following pairs
                * `id` - id of the package
                * `title` - title of the package
        * Notes - this is a search method, including the search parameter will include all packages that have the input string as a substring

* `/api/v1/<package_name>`
    * method - POST
        * content_type - multipart/form-data
        * file `json` - (ran into trouble with werkzeug on this, so it has a weird API)
            * `filename` should contain json parameters 
                * `tag` - Required, string text tag (cannot contain '/')
            * pass as type `application/json`
            * data is ignored
        * file `file`
            * pass file wanting to upload, could be `application/octet-stream` or `text/plain`
        * headers
            * `token` - token from get_token
        * response codes
            * `200` - Success
            * `400` - Invalid Use typically did not include above inputs or file
            * `401` - Unauthorized typically token is incorrect
            * `409` - Conflict, typically something that needs to be unique is not
            * `500` - Internal Server Error
        * response json (I had the thought of using these id's as an alternate accessor of the API, didn't pursue)
            * `package_id` - id of the package
            * `tag_id` - id of the tag
        * Notes - this is a very crazy API.  I tried to figure out why werkzeug was not allowing me to do this in a
          sane way, but I ran out of time.  I tried a ton of different options, but just settled for getting it working.
    * method - GET
        * content_type - application/json
        * headers
            * `token` - token from get_token
        * json inputs
            * `search` - optional, string/text, if not included will return all packages
        * response codes
            * `200` - Success
            * `401` - Unauthorized typically token is incorrect
            * `404` - Not Found, one of the url parameters is incorrect/references something not present
            * `500` - Internal Server Error
        * response json
            * list of the following pairs
                * `id` - id of the package
                * `tag` - tag for a specific instance of this package
        * Notes - this is a search method, including the search parameter will include all tags that have the input string as a substring

* `/api/v1/<package_name>/<tag>`
    * method - POST
        * content_type - multipart/form-data
        * file `json` - (ran into trouble with werkzeug on this, so it has a weird API)
            * `filename` should contain json parameters 
            * pass as type `application/json`
            * data is ignored
        * file `file`
            * pass file wanting to upload, could be `application/octet-stream` or `text/plain`
        * headers
            * `token` - token from get_token
        * response codes
            * `200` - Success
            * `400` - Invalid Use typically did not include above inputs or file
            * `401` - Unauthorized typically token is incorrect
            * `409` - Conflict, typically something that needs to be unique is not
            * `500` - Internal Server Error
        * response json (I had the thought of using these id's as an alternate accessor of the API, didn't pursue)
            * `package_id` - id of the package
            * `tag_id` - id of the tag
        * Notes - this is a very crazy API.  I tried to figure out why werkzeug was not allowing me to do this in a
          sane way, but I ran out of time.  I tried a ton of different options, but just settled for getting it working.
    * method - GET
        * content_type - application/json
        * headers
            * `token` - token from get_token
        * json inputs
            * `search` - optional, string/text, if not included will return all packages
        * responses
            * Failure response is json
                * response codes
                    * `401` - Unauthorized typically token is incorrect
                    * `404` - Not Found, one of the url parameters is incorrect/references something not present
                    * `500` - Internal Server Error
            * success is simply the data of the file in the response data section
        * Notes - This is a bit of a weird method as well.  the failure case will include the json response code, but
          the success case will use the basic python methods.  These seem to not send the response code, and thus
          it is detected by the absense of a response code.

