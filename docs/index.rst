.. _server-index:

============
FIRST Server
============
A public, freely available server is located at first-plugin.us. The below information goes into how to stand up your own FIRST server. Keep in mind the current authorization mechanism is OAuth2 from Google. This can be expanded to include other OAuth2 services, however, it is important to keep in mind that OAuth2 authorization requires a developer/app/project specific data to enable. Furthermore, Google's OAuth will only redirect to localhost or a domain name.

Installing
==========
.. note::

    To quickly install FIRST, we use Docker. Install `Docker <https://docs.docker.com/engine/installation/binaries/#/get-the-docker-engine-binaries>`_ before following the below instructions.

Installing your own FIRST server can be quick and easy with an Ubuntu machine and docker. The below instructions will use Docker to install FIRST, its dependencies, configure Apache, and create self signed certs. This is more of a production type build, if you wish to install FIRST in a developer environment then you might want to leverage Django's development server (scroll down for instructions). To install, enter the below commands into a shell.

.. important::

    **After cloning the Git repo**

    Save your google auth json information to install/google_secret.json

    Optionally, you can add install/ssl/apache.crt and apache.key file if you have an SSL certificate you would prefer to use.

.. code::

    $ apt-get install docker
    $ git clone https://github.com/vrtadmin/FIRST-server.git
    $ cd FIRST-server
    $ docker-compose -p first up -d

When the FIRST server is installed, no engines are installed. FIRST comes with three Engines: ``ExactMatch``, ``MnemonicHashing``, and ``BasicMasking``. Enable to engines you want active by using the ``utilities/engine_shell.py`` script.

.. note::

    Before engines can be installed, the developer must be registered with the system. Ensure the developer is registered before progressing.

Python script ``engine_shell.py`` can be provided with command line arguments or used as a shell. To quickly install the three available engines run the below commands:

.. code::

    $ cd FIRST-server/server/utilities
    $ python engine_shell.py install first.engines.exact_match ExactMatchEngine <developer_email>
    $ python engine_shell.py install first.engines.mnemonic_hash MnemonicHashEngine <developer_email>
    $ python engine_shell.py install first.engines.basic_masking BasicMaskingEngine <developer_email>

Once an engine is installed you can start using your FIRST installation to add and/or query for annotations. Without engines FIRST will still be able to store annotations, but will never return any results for query operations.

.. attention:: Manually installing FIRST

    FIRST can be installed manually without Docker, however, this will require a little more work. Look at docker's ``install/requirements.txt`` and install all dependencies. Afterwards, install the engines you want active (see above for quick engine installation) and run:

    .. code::

        $ cd FIRST-server/server
        $ python manage.py runserver 0.0.0.0:1337

.. _server-docs:

.. toctree::
   :maxdepth: 2
   :caption: Server Documentation

   restful-api
   engines/index
   dbs/index
