**********************************************
RMG Website - A Django-powered website for RMG
**********************************************

Authors: Prof. William H. Green (whgreen@mit.edu) and the RMG Team (rmg_dev@mit.edu)

This repository contains the source code that powers the RMG website, which
runs at http://rmg.mit.edu/. The RMG website itself uses the 
`Django <http://www.djangoproject.com/>`_ web framework.

User Setup
==========

If you only wish to *use* the RMG website, no setup is required! Simply point
your favorite web browser to http://rmg.mit.edu/ to get started. Some parts of
the web site require that Javascript be enabled.

Developer Setup
===============

The dependencies required to develop the RMG website are:

Django (http://www.djangoproject.com/)
    Version 1.2.0 or later is recommended.

RMG-Py  (http://github.com/GreenGroup/RMG-Py)
    Development of the website closely mirrors that of RMG-Py, and in general
    you will need to checkout and update the RMG-Py repository whenever you
    update this repository.

Pydot (http://code.google.com/p/pydot/)
    This can be installed via `pip install pydot` (or `easy_install pydot`).
    
Once you have successfully installed the above dependencies, fork and/or clone 
the git repository to your machine. At this point you will need a few more
dependencies:

jQuery (http://jquery.com/)
    Version 1.4.0 or later is recommended. For development you probably want
    the development (uncompressed) version. For a production environment you
    will want the minified and gzipped version. This file should be placed in
    the ``rmgweb/media`` folder.
    
jsMath (http://www.math.union.edu/~dpvc/jsMath/)
    Version 3.5 or later is recommended. These files should be placed in
    the ``rmgweb/media/jsMath`` folder. You will also need to either download
    and install the TeX fonts (recommended) or the jsMath image fonts in order 
    to see the formulas properly in your web browser.
    
Highcharts (http://www.highcharts.com/)
    This should live in a ``rmgweb/media/Highcharts`` folder.

In order to get the web server running, you must first create a secret key for
Django. This key should be placed in the file ``rmgweb/secretkey.py``. An
example of such a file, ``rmgweb/secretkey.py.example``, is available. The
easiest way to generate a secret key is to initialize a dummy Django project
and copy its secret key from the ``settings.py`` file. If you are only 
developing locally, then you can simply move the ``rmgweb/secretkey.py.example``
file to ``rmgweb/secretkey.py``; however, in production environments you are
strongly urged to use a custom key.

Once the secret key is setup, you can start the development server to test the
website locally. To do this::

$ cd rmgweb
$ python manage.py syncdb
$ python manage.py runserver

The ``syncdb`` command may prompt you to create a superuser account, which you
must do in order to develop in portions of the website that require user
authentication.

Then navigate in your favorite web browser to http://127.0.0.1:8000/. The
website may take some time to load at first, as the RMG database must be loaded
from disk every time the web server is restarted.

License
=======

The RMG website codebase is available under the terms of the MIT/X11 license,
reproduced below::

    Copyright (c) 2011 William H. Green and the RMG Team

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

