.. _server-restful-api:

RESTful API
===========
All RESTful APIs are available to users with active and valid API keys. To get register and get an API key see :ref:`registering`. All below URLs make the assumption the FIRST server is located at FIRST_HOST. If using the public FIRST server this will be http://first-plugin-us.

All RESTful APIs require a vaild API key in the URL. For example if you were trying to test your connection to FIRST, you would perform a GET request to FIRST_HOST/api/test_connection.


.. code-block:: python

   import requests

   response = requests.get('FIRST_HOST/api/test_connection/00000000-0000-0000-0000-000000000000'})

.. code-block:: bash

   > curl FIRST_HOST/api/test_connection/00000000-0000-0000-0000-000000000000

An HTTP 401 is returned if a valid api_key is not provided as a GET variable.


Test Connection
---------------
Used to test and ensure the FIRST client can connect to, validate the API key, and received the expected response.

Client Request

+--------+--------------------------------+-----------------------------+
| METHOD | URL                            | Params                      |
+========+================================+=============================+
| GET    | /api/test_connection/<api_key> | **api_key**: user's API key |
+--------+--------------------------------+-----------------------------+

Server Response

.. code-block:: json

   {"status" : "connected"}


Plugin Version Check
--------------------
Used to check if the client is using the latest version of FIRST.

.. danger::

   TODO: Implement and document [currently just planning]

Client Request

+--------+----------------------+-----------------------------+
| METHOD | URL                  | Params                      |
+========+======================+=============================+
| GET    | /api/plugin/check    | **api_key**: user's API key |
|        |                      +-----------------------------+
|        |                      | **type**: client type       |
|        |                      +-----------------------------+
|        |                      | **v**: version information  |
+--------+----------------------+-----------------------------+

Param **type**

+-----------+--------------------------+
| idapython | Hex Ray's IDA Pro plugin |
+-----------+--------------------------+
| python    | Python module            |
+-----------+--------------------------+
| radare    | Radare plugin            |
+-----------+--------------------------+
| viper     | Viper plugin             |
+-----------+--------------------------+


Get Architectures
-----------------
An HTTP 401 is returned if a valid api_key is not provided as a GET variable.

Client Request

+--------+-------------------------------------+-----------------------------+
| METHOD | URL                                 | Params                      |
+========+=====================================+=============================+
| GET    | /api/sample/architectures/<api_key> | **api_key**: user's API key |
+--------+-------------------------------------+-----------------------------+

Server Response::

   # Successful
   {"failed" : false, "architectures" : ['intel32', 'intel64', 'arm', 'arm64', 'mips', 'ppc', 'sparc', 'sysz', ...]}

   # Failed - Error
   {"failed" : true, "msg" : <String>}


Sample Checking
---------------
An HTTP 401 is returned if a valid api_key is not provided as a GET variable.

Client Request

+--------+--------------------------------+-----------------------------+
| METHOD | URL                            | Params                      |
+========+================================+=============================+
| POST   | /api/sample/checkin/<api_key>  | **api_key**: user's API key |
+--------+--------------------------------+-----------------------------+

::

   {
      #   Required
      'md5' : /^[a-fA-F\d]{32}$/,
      'crc32' : <32 bit int>,

      #   Optional
      'sha1': /^[a-fA-F\d]{40}$/,
      'sha256': /^[a-fA-F\d]{64}$/
   }


Server Response::

   # Successful
   {"failed" : false, "checkin" : true}

   # Successful -
   {"failed" : false, "checkin" : false}

   # Failed - Error
   {"failed" : true, "msg" : <String>}


+-------------------------------+------------------------------------------+
| Failure Strings               | Description                              |
+===============================+==========================================+
| Sample info not provided      | MD5/CRC32 not provided                   |
+-------------------------------+------------------------------------------+
| MD5 is not valid              | MD5 should be 32 hex characters          |
+-------------------------------+------------------------------------------+
| CRC32 value is not an integer | Integer value is required for the CRC32  |
+-------------------------------+------------------------------------------+
| Unable to connect to FIRST DB | Connection could not be established      |
+-------------------------------+------------------------------------------+


Upload Metadata
---------------

Client Request

+--------+--------------------------------+-----------------------------+
| METHOD | URL                            | Params                      |
+========+================================+=============================+
| POST   | /api/metadata/add/<api_key>    | **api_key**: user's API key |
+--------+--------------------------------+-----------------------------+

::

   {
      'md5' : /^[a-fA-F\d]{32}$/,
      'crc32' : <32 bit int>,

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

Server Response


Get Metadata History
--------------------

Client Request


+--------+---------------------------------+-----------------------------+
| METHOD | URL                             | Params                      |
+========+=================================+=============================+
| POST   | /api/metadata/history/<api_key> | **api_key**: user's API key |
+--------+---------------------------------+-----------------------------+

::

   {
      'metadata' : List of Metadata IDs (max_length = 20)
                  [<metadata_id>, ... ]
   }

Server Response

::

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





Apply Metadata
--------------

Client Request


+--------+---------------------------------+-----------------------------+
| METHOD | URL                             | Params                      |
+========+=================================+=============================+
| POST   | /api/metadata/applied/<api_key> | **api_key**: user's API key |
+--------+---------------------------------+-----------------------------+

::

   {
      'md5' : /^[a-fA-F\d]{32}$/
      'crc32' : <32 bit int>

      'id' : /^[\da-f]{24}$/
   }

Server Response



Unapply Metadata
----------------

Client Request


+--------+-----------------------------------+-----------------------------+
| METHOD | URL                               | Params                      |
+========+===================================+=============================+
| POST   | /api/metadata/unapplied/<api_key> | **api_key**: user's API key |
+--------+-----------------------------------+-----------------------------+

::

   {
      'md5' : /^[a-fA-F\d]{32}$/
      'crc32' : <32 bit int>

      'id' : /^[\da-f]{24}$/
   }

Server Response





Get Metadata
------------

Client Request


+--------+--------------------------------+-----------------------------+
| METHOD | URL                            | Params                      |
+========+================================+=============================+
| POST   | /api/metadata/get/<api_key>    | **api_key**: user's API key |
+--------+--------------------------------+-----------------------------+

::

   {
     'metadata' : List of Metadata IDs (max_length = 20)
             [<metadata_id>, ... ]
   }

Server Response





Delete Metadata
---------------

Client Request


+--------+-------------------------------------+-----------------------------+
| METHOD | URL                                 | Params                      |
+========+=====================================+=============================+
| GET    | /api/metadata/delete/<api_key>/<id> | **api_key**: user's API key |
|        |                                     +-----------------------------+
|        |                                     | **id**: metadata id         |
+--------+-------------------------------------+-----------------------------+


Server Response





Get Metadata Created
--------------------

Client Request

+--------+----------------------------------------+-----------------------------+
| METHOD | URL                                    | Params                      |
+========+========================================+=============================+
| GET    | /api/metadata/created/<api_key>        | **api_key**: user's API key |
+--------+----------------------------------------+-----------------------------+
| GET    | /api/metadata/created/<api_key>/<page> | **api_key**: user's API key |
|        |                                        | **page**: page to grab      |
+--------+----------------------------------------+-----------------------------+


Server Response

::

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





Scan for Similar Functions
--------------------------

Client Request

+--------+--------------------------------+-----------------------------+
| METHOD | URL                            | Params                      |
+========+================================+=============================+
| POST   | /api/metadata/scan/<api_key>   | **api_key**: user's API key |
+--------+--------------------------------+-----------------------------+

::

   {
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

Server Response
