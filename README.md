TheVPN
============
TheVPN is a set of scripts and web applications to manage a Dynamic VPN between multiple routers.

It can be used to fake a DM-VPN or GET-VPN like setup where tunnels are created between all members and dynamic routing is used between all members.

Supported Devices
=================
Currently the following devices / operating systems have been tested and confirmed working

* Mikrotik RouterOS 6.36

Install
=======
Clone & enter repository
```
git clone https://github.com/welbymcroberts/thevpn.co.uk
cd thevpn.co.uk/web/
```
Check Python requirements
```
pip install --upgrade -r requirements.txt
```
Set your localsettings and create secret for SECRET_KEY
```
cp web/localsettings.py.default web/localsettings.py
cat /dev/urandom | tr -dc "a-zA-Z0-9\!@#$%^&*()_+?><~\`;'" | head -c 50 > secret.txt
chmod 400 secret.txt
```
Create database
```
./manage.py migrate
./manage.py loaddata ipam/fixture.json
```
Create admin
```
./manage.py createsuperuser
```
Create Root certificate (replace THEVPN_FQDN with the value from localsettings.py)
(see https://django-ca.readthedocs.io/en/latest/ca_management.html)
```
./manage.py init_ca --key-type RSA --key-size 4096 --expires 600 --pathlen=1 root.ca.THEVPN_FQDN /C=<Country>/O=<Organisation>
```
Lookup serial of Root certificate
```
./manage.py list_cas
```
Create Certificate Authority
```
./manage.py init_ca --key-type RSA --key-size 4096 --parent=<ROOT_SERIAL> routers.ca.thevpn.nl /C=<Country>/O=<Organisation>
```
Start the server
```
./manage.py runserver
```

Now you can login to http://127.0.0.1/admin and add Countries, RouterTypes, VPN Protocols, VPN Servers

Commercial Use
==============
This project uses the "MIT License", so this is free for use by anyone, however it is asked that if you are using this in a comercial setting that a donation is made to one of the following charities:

* Medecins Sans Frontieres (Doctors Without Borders) http://www.doctorswithoutborders.org/
* Guide Dogs for the Blind or your local equivelent
* Your local Humane Society or Animal Protection agency (SPCA)
