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
Provides universally-available template tags
"""

from django import template
register = template.Library()

###############################################################################


@register.filter
def split(str, sep):
    """
    Provides a filter to interface with the string.split() method
    """
    return str.split(sep)


@register.filter
def get_ref_tooltip(reference):
    """
    Returns a tooltip-formatted reference string
    """

    from rmgpy.data.reference import Article, Book, Thesis

    output = ''
    if isinstance(reference, Article):
        if reference.title:
            output += '"{0}"\n\n'.format(reference.title)
        output += reference.get_author_string()
        if reference.journal:
            output += '\n{0}'.format(reference.journal)
            if reference.volume:
                output += ', {0}'.format(reference.volume)
                if reference.number:
                    output += ' ({0})'.format(reference.number)
                if reference.pages:
                    output += (', p. '
                               '{0}'.format(reference.pages))
            if reference.year:
                output += ' ({0})'.format(reference.year)
    elif isinstance(reference, Book):
        if reference.title:
            output += '"{0}"'.format(reference.title)
            if reference.edition:
                output += ', {0} ed.'.format(reference.edition)
            if reference.volume:
                output += ', Vol. {0}'.format(reference.volume)
            if reference.year:
                output += ' ({0})'.format(reference.year)
            output += '\n\n'
        output += reference.get_author_string()
        if reference.publisher:
            output += '\n{0}'.format(reference.publisher)
            if reference.address:
                output += ', {0}'.format(reference.address)
    elif isinstance(reference, Thesis):
        if reference.title:
            output += '"{0}"\n\n'.format(reference.title)
        output += reference.get_author_string()
        if reference.degree:
            output += '\n{0} Thesis'.format(reference.degree)
            if reference.school:
                output += ', {0}'.format(reference.school)
        else:
            if reference.school:
                output += '\n{0}'.format(reference.school)
        if reference.year:
            output += ' ({0})'.format(reference.year)

    return output


@register.simple_tag
def settings_value(setting):
    """
    Provides a template tag for retrieving settings.
    """
    from django.conf import settings

    return getattr(settings, setting, '')
