.. _server-index:

============
FIRST Server
============

ARCHIVED PROJECT
==================

THIS PROJECT HAS BEEN ARCHIVED AND ITS ISSUE QUEUE IS LOCKED. THE PROJECT WILL BE KEPT PUBLIC ONLY FOR REFERENCE PURPORSES.

The below information goes into how to stand up your own FIRST server. Keep in mind the current authorization mechanism is OAuth2 from Google. This can be expanded to include other OAuth2 services, however, it is important to keep in mind that OAuth2 authorization requires a developer/app/project specific data to enable. Furthermore, Google's OAuth will only redirect to localhost or a domain name.

Installing
==========
.. note::

    To quickly install FIRST, we use Docker. Install `Docker <https://docs.docker.com/engine/installation/binaries/#/get-the-docker-engine-binaries>`_ before following the below instructions.

Installing your own FIRST server can be quick and easy with an Ubuntu machine and docker. The below instructions will use Docker to install FIRST, its dependencies, configure Apache, and create self signed certs. This is more of a production type build, if you wish to install FIRST in a developer environment then you might want to leverage Django's development server (scroll down for instructions). To install, enter the below commands into a shell.

.. important::

    **After cloning the Git repo**

    Save your google auth json information to install/google_secret.json. To generate a google_secret.json file you will need to go to https://console.developers.google.com, create a project, select the project, select Credentials in the left set of links under APIs & services. Once selected, select the Create credentials drop down menu and click OAuth client ID. Select Web application, and fill out the details. Set the Authorized redirect URIs to your server name with `/oauth/google`

    Examples

    .. code::

        http://localhost:8888/oauth/google
        http://first.talosintelligence.com/oauth/google

    Once created you will have the option to download the JSON file containing the generated secret. Optionally, you can add install/ssl/apache.crt and apache.key file if you have an SSL certificate you would prefer to use. (Note that docker will generate one for you when the docker image is built.)

.. important::

    **Server configuration (first_config.json)**

    Before building the docker image of FIRST-server you will need to create a configuration file under the path ``server/first_config.json``. You have an example configuration file that you can copy, under the following path: ``server/example_config.json``. This configuration file has the following contents:

    .. code::

        {
            "secret_key" : "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",

            "db_engine" : "django.db.backends.mysql",
            "db_dbname" : "first_db",
            "db_user" : "root",
            "db_password" : "password12345",
            "db_host" : "mysql",
            "db_port" : 3306,

            "debug" : true,
            "allowed_hosts" : ["localhost", "testserver"],

            "oauth_path" : "/usr/local/etc/google_secret.json"
        }

    This configuration values should just work correctly on a default local docker set up. For a production enviroment:

        * ``secret_key`` should be a random and unique value
        * ``db_user``, ``db_password``, ``db_host``, ``db_port`` should be updated to match your MySQL production database.
        * ``debug`` should be set to false
        * ``allowed_hosts`` should match the host name where you configured your server (e.g.: first.talosintelligence.com)
        * ``oauth_path`` should match the path where you have your ``google_secret.json`` file. 
 
Once you have created and downloaded your ``google_secret.json`` file, and created the ``first_config.json`` configuration file, you can proceed to build and start your FIRST-server docker image:

.. code::

    $ apt-get install docker
    $ git clone https://github.com/vrtadmin/FIRST-server.git
    $ cd FIRST-server
    $ docker-compose -p first up -d

When the FIRST server is installed, no engines are installed. FIRST comes with three Engines: ``ExactMatch``, ``MnemonicHashing``, and ``BasicMasking``. Enable to engines you want active by using the ``utilities/engine_shell.py`` script.

.. note::

    Before engines can be installed, the developer must be registered with the system. This can be accomplished through the web UI if OAuth has been setup or manually by the user_shell.py located in the utilities folder.

    .. code::

        $ cd FIRST-server/server/utilities
        $ python user_shell.py adduser <user_handle: johndoe#0001> <user email: john@doe.com>

    Ensure the developer is registered before progressing.

Use the python script ``engine_shell.py`` to quickly install the available engines.

.. code::

    $ cd FIRST-server/server/utilities
    $ python3 engine_shell.py 
    FIRST>> install first_core.engines.exact_match ExactMatchEngine <developer_email>
    FIRST>> install first_core.engines.mnemonic_hash MnemonicHashEngine <developer_email>
    FIRST>> install first_core.engines.basic_masking BasicMaskingEngine <developer_email>
    FIRST>> install first_core.engines.catalog1 Catalog1Engine <developer_email>

Once an engine is installed you can start using your FIRST installation to add and/or query for annotations. Without engines FIRST will still be able to store annotations, but will never return any results for query operations.

.. attention:: Manually installing FIRST

    FIRST can be installed manually without Docker, however, this will require a little more work. Look at docker's ``install/requirements.txt`` and install all dependencies. Afterwards, install the engines you want active (see above for quick engine installation) and run:

    .. code::

        $ cd FIRST-server/server
        $ python manage.py runserver 0.0.0.0:1337

.. note:: FreeBSD port

    FIRST also has a FreeBSD port available: https://www.freshports.org/security/py-first-server/

.. _server-docs:

.. toctree::
   :maxdepth: 2
   :caption: Server Documentation

   restful-api
   engines/index
   dbs/index
