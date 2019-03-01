
#   Python Modules
import re
import json
import binascii
from functools import wraps

#   Django Modules
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

#   FIRST Modules
from first_core import DBManager, EngineManager
from first_core.util import make_id, is_engine_metadata
from first_core.auth import  verify_api_key, Authentication, FIRSTAuthError, \
                        require_login, require_apikey


MAX_FUNCTIONS = 20
MAX_METADATA = 20
VALIDATE_IDS = lambda x: re.match('^[A-Fa-f\d]{26}$', x)

#-----------------------------------------------------------------------------
#
# Decorator functions
#
#-----------------------------------------------------------------------------
def require_md5_crc32(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        request = args[0]
        md5_hash, crc32 = request.POST.get('md5'), request.POST.get('crc32')
        if None in [md5_hash, crc32]:
            return render(request, 'rest/error_json.html',
                            {'msg' : 'Sample info not provided'})

        kwargs['md5_hash'] = md5_hash.lower()
        if not re.match('^[a-f\d]{32}$', kwargs['md5_hash']):
            return render(request, 'rest/error_json.html',
                            {'msg' : 'MD5 is not valid'})

        try:
            kwargs['crc32'] = int(crc32)
        except ValueError:
            return render(request, 'rest/error_json.html',
                            {'msg' : 'CRC32 value is not an integer'})

        return view_function(*args, **kwargs)

    return decorated_function


# Create your views here.
@require_GET
@require_apikey
def test_connection(request, user):
    return HttpResponse('{"status" : "connected"}')

@require_GET
@require_apikey
def architectures(request, user):
    db = DBManager.first_db
    if not db:
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Unable to connect to FIRST DB'})

    return HttpResponse(json.dumps({'failed' : False,
                                    'architectures' : db.get_architectures()}))

@csrf_exempt
@require_POST
@require_apikey
@require_md5_crc32
def checkin(request, md5_hash, crc32, user):
    '''
    Checks a binary in when a new binary is loaded.
    Registers the binary if it has not been seen before
    Do we want to keep this or just require all this info for other operations?
    -   Con: would cause more data to be transmitted and handled

    POST request, expects:
    {
        #   Required
        'md5' : /^[a-fA-F\d]{32}$/
        'crc32' : <32 bit int>

        #   Optional
        'sha1': /^[a-fA-F\d]{40}$/
        'sha256': /^[a-fA-F\d]{64}$/
    }
    '''
    sha1_hash = request.POST.get('sha1')
    if sha1_hash != None:
        sha1_hash = sha1_hash.lower()
        if not re.match('^[a-f\d]{40}$', sha1_hash):
            sha1_hash = None

    sha256_hash = request.POST.get('sha256')
    if sha256_hash != None:
        sha256_hash = sha256_hash.lower()
        if not re.match('^[a-f\d]{64}$', sha256_hash):
            sha256_hash = None

    db = DBManager.first_db
    if not db:
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Unable to connect to FIRST DB'})

    checked_in =  db.checkin(user, md5_hash, crc32, sha1_hash, sha256_hash)
    return HttpResponse(json.dumps({'failed' : False, 'checkin' : checked_in}))

@csrf_exempt
@require_POST
@require_apikey
@require_md5_crc32
def metadata_add(request, md5_hash, crc32, user):
    '''
    Adds/Updates metadata for a given function to the db.

    POST request, expects:
    {
        #   Required - Sample
        'md5' : /^[a-fA-F\d]{32}$/
        'crc32' : <32 bit int>

        'functions' : Dictionary of json-ed Dictionaries (max_length = 20)
                {
                    'client_id' :
                        {
                        'opcodes' : String (base64 encoded)
                        'architecture' : String (max_length = 64)
                        'name' : String (max_length = 128)
                        'prototype' : String (max_length = 256)
                        'comment' : String (max_length = 512)

                        'apis' : List of Strings (max_string_length = 64)

                        #   Optional
                        'id' : String
                        }
                }
    }
    '''
    #   Check if required keys are provided
    if not request.POST.get('functions'):
        return render(request, 'rest/error_json.html',
                        {'msg' : 'All required data was not provided'})

    try:
        functions = json.loads(request.POST.get('functions'))
    except ValueError:
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Invalid json object'})

    if (dict != type(functions)) or (MAX_FUNCTIONS < len(functions)):
        return render(request, 'rest/error_json.html', {'msg' : 'Invalid function list'})

    #   Iterate through functions to validate input, fail if something is wrong
    required_keys = {   'opcodes', 'architecture', 'name',
                        'prototype', 'comment', 'apis'}
    for client_key in functions:
        f = functions[client_key]

        if not required_keys.issubset(list(f.keys())):
            return render(request, 'rest/error_json.html',
                            {'msg' : 'Invalid function list'})

        try:
            f['opcodes'] = codecs.decode(f['opcodes'].encode(), 'base64')
        except binascii.Error as e:
            return render(request, 'rest/error_json.html',
                            {'msg' : 'Unable to decode opcodes'})

        #   TODO: Normailize architecture

        #   Ensure string lengths are enforced
        string_restrictions = { 'architecture' : 64, 'name' : 128,
                                'prototype' : 256, 'comment' : 512}
        for key, max_length in string_restrictions.iteritems():
            if max_length < len(f[key]):
                return render(request, 'rest/error_json.html',
                                {'msg' : ('Data for "{}" exceeds the maximum '
                                        'length ({})').format(key, max_length)})

        #   Ensure list of API strings are within the enforced length
        for api in f['apis']:
            if 128 < len(api):
                return render(request, 'rest/error_json.html',
                                {'msg' : ('API {} is longer than 128 bytes. '
                                        'Report issue is this is a valid '
                                        'API').format(api)})

            if not re.match('^[a-zA-Z\d_:@\?\$i\.]+$', api):
                return render(request, 'rest/error_json.html',
                                {'msg' : ('Invalid characters in API, supported'
                                        'characters match the regex /^[a-zA-Z'
                                        '\\d_:@\\?\\$\\.]+$/. Report issue if'
                                        'the submitted API valid is valid.')})

    #   All input has been validated
    db = DBManager.first_db
    if not db:
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Unable to connect to FIRST DB'})

    #   Get sample
    sample = db.get_sample(md5_hash, crc32)
    if not sample:
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Sample does not exist in FIRST'})

    db.sample_seen_by_user(sample, user)

    results = {}
    for client_key in functions:
        f = functions[client_key]

        #   Check if the id sent back is from an engine, if so skip it
        if (('id' in f) and (f['id']) and is_engine_metadata(f['id'])):
            continue;

        function = db.get_function(create=True, **f)
        if not function:
            return render(request, 'rest/error_json.html',
                            {'msg' : 'Function does not exist in FIRST'})

        if not db.add_function_to_sample(sample, function):
            return render(request, 'rest/error_json.html',
                            {'msg' : ('Unable to associate function with '
                                    'sample in FIRST')})

        metadata_id = db.add_metadata_to_function(user, function, **f)
        if not metadata_id:
            return render(request, 'rest/error_json.html',
                            {'msg' : ('Unable to associate metadata with '
                                      'function in FIRST')})

        #   The '0' indicated the metadata_id is from a user.
        _id = make_id(0, metadata=metadata_id)
        results[client_key] = _id

        #   Set the user as applying the metadata
        db.applied(sample, user, _id)

        #   Send opcode to EngineManager
        EngineManager.add(function.dump(True))

    return HttpResponse(json.dumps({'failed' : False, 'results' : results}))

@csrf_exempt
@require_POST
@require_apikey
def metadata_history(request, user):
    '''
    Returns the history of the given metadata

    POST request, expects:
    {
        #   Required
        'metadata' : List of Metadata IDs (max_length = 20)
                [<metadata_id>, ... ]
    }

    Successful returns:
    {
        'failed': False,
        'results' : Dictionary of dictionaries
                {
                    'metadata_id' : Dictionary
                            {
                                'creator' : String (max_length = 37) (/^[\s\d_]{1,32}#\d{4}$/)
                                'history : List of dictionaries
                                    [{
                                        'name' : String (max_length = 128)
                                        'prototype' : String (max_length = 256)
                                        'comment' : String (max_length = 512)
                                        'committed' : Datetime
                                    }, ...]
                            }
                }
    }
    '''
    if not request.POST.get('metadata'):
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Invalid metadata information'})

    try:
        metadata = json.loads(request.POST.get('metadata'))
    except ValueError:
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Invalid json object'})

    if MAX_METADATA < len(metadata):
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Exceeded max bulk request'})

    if None in map(VALIDATE_IDS, metadata):
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Invalid metadata id'})

    db = DBManager.first_db
    if not db:
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Unable to connect to FIRST DB'})

    results = db.metadata_history(metadata)
    return HttpResponse(json.dumps({'failed' : False, 'results' : results}))

@csrf_exempt
@require_POST
@require_apikey
@require_md5_crc32
def metadata_applied(request, md5_hash, crc32, user):
    '''
    Marks metadata as applied to a binary

    POST request, expects:
    {
        #   Required - Sample
        'md5' : /^[a-fA-F\d]{32}$/
        'crc32' : <32 bit int>

        'id' : /^[\da-f]{24}$/
    }
    '''
    _id = request.POST.get('id')
    return metadata_status_change(_id, user, md5_hash, crc32, True)

@csrf_exempt
@require_POST
@require_apikey
@require_md5_crc32
def metadata_unapplied(request, md5_hash, crc32, user):
    '''
    Unapplies metadata to binary

    POST request, expects:
    {
        #   Required - Sample
        'md5' : /^[a-fA-F\d]{32}$/
        'crc32' : <32 bit int>

        'id' : /^[\da-f]{24}$/
    }
    '''
    _id = request.POST.get('id')
    return metadata_status_change(_id, user, md5_hash, crc32, False)

@csrf_exempt
@require_POST
@require_apikey
def metadata_get(request, user):
    '''
    Returns metadata identified by id

    POST request, expects:
    {
        'metadata' : List of Metadata IDs (max_length = 20)
                [<metadata_id>, ... ]
    }
    '''
    if not request.POST.get('metadata'):
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Invalid metadata information'})

    try:
        metadata = json.loads(request.POST.get('metadata'))
    except ValueError:
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Invalid json object'})

    if ((MAX_METADATA < len(metadata))
        or (None in [VALIDATE_IDS(x) for x in metadata])):
        return render(request, 'rest/error_json.html', {'msg' : 'Invalid id value'})

    db = DBManager.first_db
    if not db:
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Unable to connect to FIRST DB'})

    results = {x['id'] : x for x in db.get_metadata_list(metadata)}

    return HttpResponse(json.dumps({'failed' : False, 'results' : results}))

@require_GET
@require_apikey
def metadata_delete(request, user, _id):
    '''
    Deletes metadata identified by id owned by person submitting request
    /api/metadata/delete/<api_key>/<metadata_id>

    '''
    if not VALIDATE_IDS(_id):
        return render(request, 'rest/error_json.html', {'msg' : 'Invalid id value'})

    db = DBManager.first_db
    if not db:
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Unable to connect to FIRST DB'})

    deleted = db.delete_metadata(user, _id)
    return HttpResponse(json.dumps({'failed' : False, 'deleted' : deleted}))

@require_GET
@require_apikey
def metadata_created(request, user, page=1):
    '''
    Returns chunks of 20 metadatas added to FIRST by user

    GET request, expects:
    /api/metadata/created/<api_key>
    /api/metadata/created/<api_key>/<page>

    Successful returns:
    {
        'failed': False,
        'page' : Integer (current page requested,
        'pages' : Integer (total number of pages)
        'results' : Dictionary of dictionaries
                {
                    'metadata_id' : Dictionary
                            {
                                'name' : String (max_length = 128)
                                'prototype' : String (max_length = 256)
                                'comment' : String (max_length = 512)
                                'rank' : Integer
                                'id' : String (length = 24)
                            }
                }
    }
    '''
    page = int(page)
    result = {'failed' : False, 'page' : page, 'results' : []}

    db = DBManager.first_db
    if not db:
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Unable to connect to FIRST DB'})

    result['results'], result['pages'] = db.created(user, page, MAX_METADATA)

    return HttpResponse(json.dumps(result))

@csrf_exempt
@require_POST
@require_apikey
def metadata_scan(request, user):
    '''
    Returns all metadata added to FIRST by user

    POST request, expects:
    {
        #   Required
        'functions' : Dictionary of json-ed Dictionaries (max_length = 20)
                {
                    'client_id' :
                                {
                                    'opcodes' : String (base64 encoded)
                                    'architecture' : String (max_length = 64)
                                    'apis' : List Strings
                                }
                }
    }
    '''
    if not request.POST.get('functions'):
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Invalid function information'})

    try:
        functions = json.loads(request.POST.get('functions'))
    except ValueError:
        return render(request, 'rest/error_json.html',
                        {'msg' : 'Invalid json object'})

    if ((dict != type(functions)) or MAX_FUNCTIONS < len(functions)):
        return render(request, 'rest/error_json.html', {'msg' : 'Invalid function json'})

    #   Validate input
    validated_input = {}
    required_keys = {'opcodes', 'apis', 'architecture'}
    for client_id, details in functions.iteritems():
        if ((dict != type(details))
            or (not required_keys.issubset(list(details.keys())))):
            return render(request, 'rest/error_json.html',
                            {'msg' : 'Function details not provided'})

        architecture = details['architecture']
        if 64 < len(architecture):
            return render(request, 'rest/error_json.html',
                            {'msg' : 'Invalid architecture'})

        #   Ensure list of API strings are within the enforced length
        for api in details['apis']:
            if 128 < len(api):
                return render(request, 'rest/error_json.html',
                                {'msg' : ('API {} is longer than 128 bytes. '
                                        'Report issue is this is a valid '
                                        'API').format(api)})

            if not re.match('^[a-zA-Z\d_:@\?\$\.]+$', api):
                return render(request, 'rest/error_json.html',
                                {'msg' : ('Invalid characters in API, supported'
                                        'characters match the regex /^[a-zA-Z'
                                        '\\d_:@\\?\\$\\.]+$/. Report issue if'
                                        'the submitted API valid is valid.')})

        try:
            opcodes = codecs.decode(details['opcodes'].encode(), 'base64')
        except binascii.Error as e:
            return render(request, 'rest/error_json.html',
                            {'msg' : 'Unable to decode opcodes'})

        validated_input[client_id] = {  'opcodes' : opcodes,
                                        'apis' : details['apis'],
                                        'architecture' : architecture}

    data = {'engines' : {}, 'matches' : {}}
    for client_id, details in validated_input.iteritems():
        results = EngineManager.scan(user, **details)
        if (not results) or (results == ({}, [])):
            continue

        engine_details, results = results
        data['engines'].update(engine_details)
        data['matches'][client_id] = results

    return HttpResponse(json.dumps({'failed' : False, 'results' : data}))



@require_apikey
def status(request, user):
    pass


#-----------------------------------------------------------------------------
#
# Helper functions
#
#-----------------------------------------------------------------------------
def metadata_status_change(_id, user, md5_hash, crc32, applied):
    if not _id:
        return render(None, 'rest/error_json.html',
                        {'msg' : 'Invalid metadata information'})

    if not VALIDATE_IDS(_id):
        return render(None, 'rest/error_json.html',
                        {'msg' : 'Invalid id value'})

    db = DBManager.first_db
    if not db:
        return render(None, 'rest/error_json.html',
                        {'msg' : 'Unable to connect to FIRST DB'})

    #   Get sample
    sample = db.get_sample(md5_hash, crc32)
    if not sample:
        return render(None, 'rest/error_json.html',
                        {'msg' : 'Sample does not exist in FIRST'})

    if applied:
        results = db.applied(sample, user, _id)
    else:
        results = db.unapplied(sample, user, _id)

    return HttpResponse(json.dumps({'failed' : False, 'results' : results}))
