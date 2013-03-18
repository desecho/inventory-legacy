#Inventory

The web application to manage storage. The interface is in Russian.
You can create boxes of type 5 and 6 by using administration panel.

##Required packages

* [Python 2](http://www.python.org)
* [Django 1.5](http://djangoproject.com)
* [django-annoying](https://github.com/skorokithakis/django-annoying)
* [django-bootstrap-toolkit](https://github.com/dyve/django-bootstrap-toolkit)

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

* Change the following variables in settings.py. You'll need an API key. You can obtain it here - http://api.themoviedb.org. Make sure that the user running the server has access to write to /cache/tmdb3.cache. You can generate SECRET_KEY using [Django Secret Key Generator](http://www.miniwebtool.com/django-secret-key-generator/). Insert your path to django admin static directory to STATICFILES_DIRS. It should be like something like '/usr/local/lib/python2.7/dist-packages/django/contrib/admin/static'
    * DATABASES
    * SECRET_KEY
    * BASE_PATH
    * STATICFILES_DIRS

* Run
```
python manage.py syncdb
python manage.py collectstatic
```

* Import db.sql to your database
