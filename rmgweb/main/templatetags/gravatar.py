#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#                                                                             #
# RMG Website - A Django-powered website for Reaction Mechanism Generator     #
#                                                                             #
# Copyright (c) 2011-2018 Prof. William H. Green (whgreen@mit.edu),           #
# Prof. Richard H. West (r.west@neu.edu) and the RMG Team (rmg_dev@mit.edu)   #
#                                                                             #
# Permission is hereby granted, free of charge, to any person obtaining a     #
# copy of this software and associated documentation files (the 'Software'),  #
# to deal in the Software without restriction, including without limitation   #
# the rights to use, copy, modify, merge, publish, distribute, sublicense,    #
# and/or sell copies of the Software, and to permit persons to whom the       #
# Software is furnished to do so, subject to the following conditions:        #
#                                                                             #
# The above copyright notice and this permission notice shall be included in  #
# all copies or substantial portions of the Software.                         #
#                                                                             #
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,    #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER      #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING     #
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER         #
# DEALINGS IN THE SOFTWARE.                                                   #
#                                                                             #
###############################################################################

"""
Provides a template tag for retrieving the Gravatar for a given email. Gravatar
is a web service providing cross-site avatar and profile management.

To enable this tag, add the line ::

{% load gravatar %}

to the top of the template. The syntax of the gravatar template tag is ::

{% gravatar <email> [size] %}

where `email` is the email address you wish to fetch the gravatar for, and
`size` is the (optional) size of the fetched avatar.
"""

from future import standard_library
standard_library.install_aliases()

import re
import hashlib
import urllib

from django import template
from django.contrib.auth.models import User

register = template.Library()

email_search = re.compile('(\w+\@[^> ]+)')


@register.simple_tag
def gravatar(username, size=48):
    """
    Return an <img> tag with the Gravatar for the given `username`. The image
    `size` defaults to 48 x 48 when not specified. To use, add
    ``{% load gravatar %}`` to the top of the template, then use the syntax
    ``{% gravatar <email> [size] %}``.
    """
    match = email_search.search(username)
    if match:
        email = match.group()
    else:
        # this may fail badly if the username is not in the database
        email = User.objects.get(username=username).email

    url = "http://www.gravatar.com/avatar.php?"
    url += urllib.parse.urlencode({
        'gravatar_id': hashlib.md5(email).hexdigest(),
        'size': size,
        'default': 'wavatar',
    })

    return """<img src="%s" width="%s" height="%s" alt="gravatar" class="gravatar" border="0" />""" % (url, size, size)
