Installation guide
==================

These are the instructions for doing a manual installation of the new 0.9 release that runs under mod_wsgi, geared towards Linux, tested on Debian, Ubuntu, and CentOS.

System Requirements

    * Python 2.5 or later
    * Linux (known to work on Ubuntu, Debian, CentOS) or BSD (people have got it working)


WikiPBX Core
------------

Download/Checkout Code
++++++++++++++++++++++

The code is normally extracted or checked to a wikipbx subdirectory under /usr/src, which this document will assume. In fact you can put it wherever you want::

  $ cd /usr/src

You can get the 0.9.0 release tarball::

  $ wget http://www.wikipbx.org/releases/wikipbx-0.9.0.tar.gz
  $ tar xvfz wikipbx-0.9.0.tar.gz

Or you can checkout directly from Launchpad::

  $ bzr co lp:~wikipbx-dev/wikipbx/0.9.x wikipbx

Install Code
++++++++++++

If you want, you can "install" the code somewhere different than where you downloaded it. However, these instructions just assume you are Extremely Lazy, and just leave it where it already is!

This document will assume the code will be in the wikipbx subdirectory in /usr/src, so you should have a file /usr/src/wikipbx/wikipbx/settings_template.py (yes, there are two wikipbx directories, that is not a typo)

Settings Template
+++++++++++++++++

After installing wikipbx, the first thing you need to do is create a custom settings.py that will be edited later::

  $ cd /usr/src/wikipbx/wikipbx
  $ cp settings_template.py settings.py

settings_template.py should never be changed! Changes for your specific installation must be done in settings.py, NOT settings_template.py

The following settings are needed for CDR's to be correctly posted back to WikiPBX and get written to the filesystem.

    * edit settings.py in your preferred text editor
    * modify FREESWITCH_URL_PORT and change the current value to http://wikipbx.yourserver.net, where yourserver.net MUST be replaced with the domain name you are planning on using.
    * mkdir -p /var/log/wikipbx/cdr/err
    * modify directory specifed in LOG_DIR_ROOT and subdirectory permissions so that the user under which freeswitch process will run has write access to that directory

The remaining settings that must be customized (such as the database settings), will be done later in the installation. Most values in this file can and should be left as the default values. If you're not sure what some of the settings mean, django settings documentation can help.

Database Adaptor
----------------

Default settings template is configured to use SQLite database backend. It's sufficient for demoing and doesn't require extra libraries. For serious load you should choose a more advanced DB backend. PostgreSQL is the preferred DB backend, but anything that `django supports <http://docs.djangoproject.com/en/1.2/ref/databases/>`_ should work as well. Instructions for setting up PostgreSQL database are provided in :doc:`postgres`.


Update Settings
---------------

After a database user and database have been created, update the settings.py file to reflect these values. If you don't do this, the next step will fail.

Initialize Database
-------------------

::

  $ cd /usr/src/wikipbx
  $ python manage.py syncdb --noinput

the output should look like::

  Creating table auth_message
  ...
  Creating table django_content_type
  Installing index for wikipbxweb.UserProfile model
  ...
  Installing index for auth.Message model

FreeSWITCH
----------

If you don't already have FreeSWITCH installed, you will need to install it. Please see the FreeSWITCH installation guide for installing FreeSWITCH.

The latest version of FreeSWITCH that has been tested is 15699 which was released on (28 Nov 2009). Later versions of FreeSWITCH should work without any problem. As far as earlier versions tested, FreeSWITCH 13501 is known to work fine. Earlier versions will most likely also work.
Enable Modules - Compile Time

Modules are enabled by editing the modules.conf file and uncommenting or adding the appropriate lines. modules.conf appears in the root of the FreeSWITCH source tree (eg, /usr/src/freeswitch), but only '''after''' 'configure' has been run.

The following '''modules''' must be built and enabled:

    * mod_event_socket
    * mod_xml_curl
    * mod_xml_cdr

Rebuild + Install
+++++++++++++++++

After the modules.conf file has been changed, freeswitch must be rebuilt:

 make install

Configure Loaded Modules
++++++++++++++++++++++++

Open the file /usr/local/freeswitch/conf/autoload_configs/modules.conf.xml

Uncomment all the following modules::

  <load module="mod_event_socket"/>  
  <load module="mod_xml_curl"/>
  <load module="mod_xml_cdr"/>

Configure mod_xml_curl

Change the file /usr/local/freeswitch/conf/xml_curl.conf.xml::

  <configuration name="xml_curl.conf" description="cURL XML Gateway">
    <bindings>
      <binding name="example">
        <!-- The url to a gateway cgi that can generate xml similar to
             what's in this file only on-the-fly (leave it commented if you dont
             need it) -->
        <!-- one or more |-delim of configuration|directory|dialplan -->
        <param name="gateway-url" value="http://wikipbx.yourserver.net/xml_dialplan/" bindings="configuration,dialplan,directory"/>
        <!-- set this to provide authentication credentials to the server -->
        <!--<param name="gateway-credentials" value="muser:mypass"/>-->
      </binding>
    </bindings>
  </configuration>

You will also need to make sure that mod_xml_curl was enabled in modules.conf before compiling FreeSWITCH, and that it is enabled for runtime loading in modules.conf.xml. See mod_xml_curl for detailed instructions.

Build ESL with Python Bindings
++++++++++++++++++++++++++++++

ESL is the socket library used from the Web Server code to communicate with freeswitch

Change directory to libs/esl directory under freeswitch source tree

NOTE: If you are running an older version of FreeSWITCH, you will first need to manually edit python/Makefile to use the version of python you prefer to use. When you open that file it should be clear how to modify it, it's a small file::

  $ make pymod

Start Services
--------------

Start Apache2
+++++++++++++

WikiPBX must be started before FreeSWITCH, so that FreeSWITCH can pull the configuration from WikiPBX::

  $ /etc/init.d/apache2 restart

To view logs::

  $ tail -f /var/log/apache2/error.log /var/log/apache2/wikipbx.yourserver.net-error.log

Start Freeswitch::

  $ cd /usr/loca/freeswitch/bin
  $ ./freeswitch

Verify Installation
-------------------

Home Page
+++++++++

Navigate to http://wikipbx.yourserver.net

You should see a link under the login section that says '''[Add Root]'''.
FreeSWITCH configuration

    * Type "sofia status" on the freeswitch console
    * Verify that you see the sip profile(s) you created in WikiPBX listed, and no others.

FreeSWITCH connectivity
+++++++++++++++++++++++

    * Create a root user
    * Create an account and initial account admin
    * Login as the account admin
    * Click "Live Calls" link on the left toolbar — you should not see any errors
