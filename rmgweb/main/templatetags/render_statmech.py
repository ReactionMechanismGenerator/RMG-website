#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
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
################################################################################

"""
Provides template tags for rendering transport  models in various ways.
"""

# Register this module as a Django template tag library
from django import template
register = template.Library()

from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

import numpy

from rmgweb.main.tools import getLaTeXScientificNotation, getStructureMarkup
from rmgweb.main.models import UserProfile

from rmgpy.quantity import Quantity
from rmgpy.data.statmech import *

################################################################################

@register.filter
def render_statmech_math(statmech, user=None):
    """
    Return a math representation of the given `transport` using MathJax. If a
    `user` is specified, the user's preferred units will be used; otherwise 
    default units will be used.
    """
    
    # The string that will be returned to the template
    result = ''
    
    if isinstance(statmech, GroupFrequencies):
        
        result += '<table class="statmechEntryData">\n'
                
        if statmech.frequencies is not None:
            result += r'    <td class = "key"><span>Group Frequencies</span>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class = "key"><span>Lower Bound</span>'
            result += r'    <td class = "key"><span>Upper Bound</span>'
            result += r'    <td class = "key"><span>Degeneracy</span>'
            for row in statmech.frequencies:  
                result += '<tr>\n'    
                result += r'    <td class = "key"><span></span>'
                result += r'    <td class = "key"><span></span>'                
                result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(row[0], '')
                result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(row[1], '')
                result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(row[2], '')
                result += '</tr>'
            result += '</td>\n'
        
        if statmech.symmetry is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Symmetry</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(statmech.symmetry, '')
            result += '</tr>\n'

        result += '</table>\n'

    return mark_safe(result)
