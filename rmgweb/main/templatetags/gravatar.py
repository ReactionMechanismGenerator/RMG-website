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

import urllib
import hashlib
from django import template

register = template.Library()

@register.simple_tag
def gravatar(email, size=48):
    """
    Return an <img> tag with the Gravatar for the given `email`. The image
    `size` defaults to 48 x 48 when not specified. To use, add 
    ``{% load gravatar %}`` to the top of the template, then use the syntax
    ``{% gravatar <email> [size] %}``.
    """

    url = "http://www.gravatar.com/avatar.php?"
    url += urllib.urlencode({
        'gravatar_id': hashlib.md5(email).hexdigest(),
        'size': str(size),
        'default': 'wavatar',
    })

    return """<img src="%s" width="%s" height="%s" alt="gravatar" class="gravatar" border="0" />""" % (url, size, size)
