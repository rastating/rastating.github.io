---
layout: single
title: Setting Up Kali for Metasploit Unit Testing
date: 2015-02-28
categories:
  - security
tags:
  - metasploit
---
This past week, I have been working on a new module for Metasploit which required a change to one of the core library files. As a result, I had to update the RSpec tests for that particular module. This was my first time running the unit tests in Metasploit, as I had previously not had to change any library files, however, it didn't go as smoothly as anticipated!

The [Development Environment Setup Guide](https://github.com/rapid7/metasploit-framework/wiki/Setting-Up-a-Metasploit-Development-Environment) does state that Kali is not the best platform to be using for development purposes; however, if you want to use it and you are having issues running unit tests, read on!

*N.B: if you're interested in reading some of the discussions that led to this final set of steps, see [This Pull Request](https://github.com/rapid7/metasploit-framework/pull/4789)*

## Ensure all required packages are installed
Ensure that all the packages specified in the [Development Environment Setup Guide](https://github.com/rapid7/metasploit-framework/wiki/Setting-Up-a-Metasploit-Development-Environment) have been installed. As of 28th February 2015, this can be done using the following commands (I'd recommend reading the guide though in case this changes in the future):

**Various required packages**
```bash
sudo apt-get -y install \
  build-essential zlib1g zlib1g-dev \
  libxml2 libxml2-dev libxslt-dev locate \
  libreadline6-dev libcurl4-openssl-dev git-core \
  libssl-dev libyaml-dev openssl autoconf libtool \
  ncurses-dev bison curl wget postgresql \
  postgresql-contrib libpq-dev \
  libapr1 libaprutil1 libsvn1 \
  libpcap-dev libsqlite3-dev
```

**RVM (if GPG signature verification fails, just follow the instructions you see on screen)**
```bash
\curl -L https://get.rvm.io | bash -s stable --autolibs=enabled --ruby=2.1.5
```

**Load RVM scripts**
```bash
source /usr/local/rvm/scripts/rvm
```

## Get the source code and required gems
Grab the latest source code from GitHub by running:

```bash
cd ~/
git clone https://github.com/rapid7/metasploit-framework.git
```

Once cloned, we need to set our environment up to use Ruby 2.1.5 and install the required Ruby gems:

```bash
cd ~/metasploit-framework &&
rvm install 2.1.5 &&
rvm --create --versions-conf use 2.1.5@metasploit-framework &&
pushd ..; popd &&
bundle install
```

## Setup PostgreSQL to work with Metasploit
The RSpec tests [currently] require a database connection, so we need to first ensure we have a user for production / development purposes and one for testing purposes and also make some necessary configuration changes to PostgreSQL itself.

There are various means of doing all of these things, however, the only way that worked for me using the out of the box installation of PostgreSQL that comes with Kali was the following:

**Ensure the PostgreSQL service is running**
```bash
service postgresql start
```

**Run psql as the postgres user**
```bash
sudo -u postgres psql
```

**Change the default encoding of new databases to UTF-8 as opposed to SQL_ASCII**
```sql
UPDATE pg_database SET datistemplate = FALSE WHERE datname = 'template1';
DROP DATABASE template1;
CREATE DATABASE template1 WITH TEMPLATE = template0 ENCODING = 'UNICODE';
UPDATE pg_database SET datistemplate = TRUE WHERE datname = 'template1';
```

You can verify the previous step by typing `\l` at the psql prompt and checking the template1 encoding value; it should now read UTF8:

```bash
postgres=# \l
                             List of databases
   Name    |  Owner   | Encoding  | Collate | Ctype |   Access privileges
-----------+----------+-----------+---------+-------+-----------------------
 postgres  | postgres | SQL_ASCII | C       | C     |
 template0 | postgres | SQL_ASCII | C       | C     | =c/postgres          +
           |          |           |         |       | postgres=CTc/postgres
 template1 | postgres | UTF8      | C       | C     |
(3 rows)
```

**Create the new users**
```sql
CREATE USER msf WITH PASSWORD 'msf' CREATEDB;
CREATE USER msftest WITH PASSWORD 'msftest' CREATEDB;
```

**Create the new databases**
```sql
CREATE DATABASE msf OWNER msf;
CREATE DATABASE msftest OWNER msftest;
```

*N.B. to exit psql, type `\q`*

## Configure database.yml in Metasploit
The next step is to configure the file that Metasploit will use when establishing connections to PostgreSQL. Start by copying the example config file:

```bash
cd ~/metasploit-framework/config &&
cp database.yml.example database.yml
```

Now, open `database.yml` in your preferred editor, and set the database, username and password fields in the development and test sections to match those that we created in the previous steps. Once done, your file should look similar to this:

```yaml
# Please only use postgresql bound to a TCP port.
# Only postgresql is supportable for metasploit-framework
# these days. (No SQLite, no MySQL).
#
# To set up a metasploit database, follow the directions hosted at:
# https://fedoraproject.org/wiki/Metasploit_Postgres_Setup (Works on
# essentially any Linux distro, not just Fedora)
development: &pgsql
  adapter: postgresql
  database: msf
  username: msf
  password: msf
  host: localhost
  port: 5432
  pool: 5
  timeout: 5

# You will often want to seperate your databases between dev
# mode and prod mode. Absent a production db, though, defaulting
# to dev is pretty sensible for many developer-users.
production: &production
  <<: *pgsql

# Warning: The database defined as "test" will be erased and
# re-generated from your development database when you run "rake".
# Do not set this db to the same as development or production.
#
# Note also, sqlite3 is totally unsupported by Metasploit now.
test:
  <<: *pgsql
  database: msftest
  username: msftest
  password: msftest
```

## Moment of truth...
First, run the following command to do any required migration:

```bash
cd ~/metasploit-framework &&
rake db:migrate
```

And now, let's try running the unit tests by running:

```bash
rake spec
```

If all goes well, you will now be running the unit tests. In addition to running all of them using the above command, you can run individual tests too, such as:

```bash
rspec spec/lib/msf/http/wordpress/version_spec.rb
```

## Thanks to...
[@FireFart](https://twitter.com/_FireFart_), [@kernelsmith](https://twitter.com/kernelsmith) and [Brent Cook](https://github.com/bcook-r7) for their help piecing together this information; without their assistance I'd probably have still been banging my head into the keyboard.
