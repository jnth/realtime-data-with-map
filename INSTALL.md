# Install and deploy this application on an Apache 2.4+ server

__Example of installation on an Ubuntu Server.__

This application use Python 3, PostgreSQL, Apache 2.4+ and `mod_wsgi` Apache library.

    sudo apt install python3 python3-dev python3-pip libapache2-mod-wsgi-py3

Untar application.

Install Python requirements:

    sudo pip3 install -r requirements.txt

Or

    pip3 install -r requirements.txt --local
    
Create a PostgreSQL database and set connection configuration in `dbinfo.py`.

Create database schema `qa` and tables by running `init-db.sql` in your database.

Configure Apache (`/etc/apache2/sites-available/afficheur-qa.conf`) :

    <VirtualHost *:9876>
        ServerName example.com

        # Log
        ErrorLog ${APACHE_LOG_DIR}/afficheur-qa-error.log
        CustomLog ${APACHE_LOG_DIR}/afficheur-qa-access.log combined

        WSGIDaemonProcess application user=user group=group threads=5
        WSGIScriptAlias / /path/of/afficheur-qa/realtime-data-with-map/afficheur-qa.wsgi

        <Directory /path/of/afficheur-qa/realtime-data-with-map>
            WSGIProcessGroup application
            WSGIApplicationGroup %{GLOBAL}
            Require all granted
        </Directory>
    </VirtualHost>

Do not forget to add port `9876` in Apache configuration (`/etc/apache2/ports.conf`).

Activate configuration:

    sudo a2ensite afficheur-qa.conf
    sudo a2enmod wsgi
    sudo service apache2 reload

