PostgreSQL Configuration
========================

Tested on PostgreSQL 8.x and 9.x::

  pip install psycopg2

Prepare Database
----------------

Create Database User
++++++++++++++++++++

::

  $ su - postgres
  $ createuser --pwprompt --encrypted --no-adduser wikipbxuser

When it asks you if the new user can create databases, answer YES. The other questions can be answered with NO.

Allow DB User to connect
++++++++++++++++++++++++

The default postgresql configuration requires that the connection be from the same UNIX user as the db user for local connections. If you don't want to create a UNIX user called wikipbxuser (or whatever you choose), then you will probably have to modify the postgresql configuration.

If that is the case, then edit your /etc/postgresql/X.Y/main/pg_hba.conf file to use md5 password authentication for local connections::

  #
  # Database administrative login by UNIX sockets
  #
  local   all         postgres                          md5
  #
  #
  # TYPE  DATABASE    USER        CIDR-ADDRESS          METHOD
  #
  #
  # "local" is for Unix domain socket connections only
  #
  local   all         all                               md5
  #
  # IPv4 local connections:
  #
  host    all         all         127.0.0.1/32          md5
  #
  # IPv6 local connections:
  #
  host    all         all         ::1/128               md5

Then restart the postgresql daemon::

  /etc/init.d/postgresql restart


Create Database
+++++++++++++++

Assuming you already have a database user named wikipbx, issue the following to create a database named wikipbx. When it prompts you for the password, enter the password you entered above when creating the wikipbx database user::

 createdb --password --owner wikipbxuser --user wikipbxuser wikipbx


