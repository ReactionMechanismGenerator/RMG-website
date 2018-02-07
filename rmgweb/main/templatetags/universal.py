#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#
#	RMG Website - A Django-powered website for Reaction Mechanism Generator
#
#	Copyright (c) 2011 Prof. William H. Green (whgreen@mit.edu) and the
#	RMG Team (rmg_dev@mit.edu)
#
#	Permission is hereby granted, free of charge, to any person obtaining a
#	copy of this software and associated documentation files (the 'Software'),
#	to deal in the Software without restriction, including without limitation
#	the rights to use, copy, modify, merge, publish, distribute, sublicense,
#	and/or sell copies of the Software, and to permit persons to whom the
#	Software is furnished to do so, subject to the following conditions:
#
#	The above copyright notice and this permission notice shall be included in
#	all copies or substantial portions of the Software.
#
#	THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#	DEALINGS IN THE SOFTWARE.
#
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
            output += '"{0}"\n\n'.format(reference.title.encode('utf-8'))
        output += reference.getAuthorString().encode('utf-8')
        if reference.journal:
            output += '\n{0}'.format(reference.journal.encode('utf-8'))
            if reference.volume:
                output += ', {0}'.format(reference.volume.encode('utf-8'))
                if reference.number:
                    output += ' ({0})'.format(reference.number.encode('utf-8'))
                if reference.pages:
                    output += (', p. '
                               '{0}'.format(reference.pages.encode('utf-8')))
            if reference.year:
                output += ' ({0})'.format(reference.year.encode('utf-8'))
    elif isinstance(reference, Book):
        if reference.title:
            output += '"{0}"'.format(reference.title.encode('utf-8'))
            if reference.edition:
                output += ', {0} ed.'.format(reference.edition.encode('utf-8'))
            if reference.volume:
                output += ', Vol. {0}'.format(reference.volume.encode('utf-8'))
            if reference.year:
                output += ' ({0})'.format(reference.year.encode('utf-8'))
            output += '\n\n'
        output += reference.getAuthorString().encode('utf-8')
        if reference.publisher:
            output += '\n{0}'.format(reference.publisher.encode('utf-8'))
            if reference.address:
                output += ', {0}'.format(reference.address.encode('utf-8'))
    elif isinstance(reference, Thesis):
        if reference.title:
            output += '"{0}"\n\n'.format(reference.title.encode('utf-8'))
        output += reference.getAuthorString().encode('utf-8')
        if reference.degree:
            output += '\n{0} Thesis'.format(reference.degree.encode('utf-8'))
            if reference.school:
                output += ', {0}'.format(reference.school.encode('utf-8'))
        else:
            if reference.school:
                output += '\n{0}'.format(reference.school.encode('utf-8'))
        if reference.year:
            output += ' ({0})'.format(reference.year.encode('utf-8'))

    return output

@register.simple_tag
def settings_value(setting):
    """
    Provides a template tag for retrieving settings.
    """
    from django.conf import settings

    return getattr(settings, setting, '')
