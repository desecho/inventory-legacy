#Inventory

The web application to manage storage. The interface is in Russian.
You can create boxes of type 5 and 6 by using administration panel.

##Required packages

* [Python v2.6.5+](http://www.python.org)
* [Django v1.5](http://djangoproject.com)
* [django-annoying v0.7.7+](https://github.com/skorokithakis/django-annoying)
* [django-bootstrap-toolkit v2.8.0+](https://github.com/dyve/django-bootstrap-toolkit)

##Used Javascript libraries
* [Bootstrap v2.3.1](http://twitter.github.com/bootstrap/)
* [jQuery v1.9.1](http://jquery.com/)
* [jQuery UI v1.10.2](http://jqueryui.com/)
* [jQuery UI Bootstrap v0.5](http://addyosmani.github.com/jquery-ui-bootstrap/)
* [Messenger v1.2.3](http://github.hubspot.com/messenger/)
    * [Backbone.js v0.9.10](http://backbonejs.org/)
    * [Underscore.js v1.4.4](http://underscorejs.org/)
* [Select2 v3.3.1](http://ivaynberg.github.com/select2/)
* [jQuery plugin: Validation v1.11.0](http://bassistance.de/jquery-plugins/jquery-plugin-validation/)
* [Datejs](http://www.datejs.com/)

##Installation instructions

* Insert your database settings in settings.py

* Run
```
python manage.py syncdb
python manage.py collectstatic
python manage.py shell
```

* Import db.sql to your database
