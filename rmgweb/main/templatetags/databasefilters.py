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
Provides template tags for rendering kinetics models in various ways.
"""

# Register this module as a Django template tag library
from django import template
register = template.Library()

from django.utils.safestring import mark_safe

import numpy

from rmgweb.main.tools import getLaTeXScientificNotation, getStructureMarkup
from rmgweb.main.models import UserProfile

from rmgpy.quantity import Quantity

################################################################################
@register.filter
def renderMW(MW):
    """
    Renders molecular weight from SI units to the regular g/mol units we are used to.
    """
    mass = Quantity(MW,'kg/mol').value
    multfactor = Quantity(1,'g/mol').getConversionFactorFromSI()
    return mark_safe(mass*multfactor)

@register.filter
def renderAdjlist(adjlist):
    """
    Renders adjacency list line by line in html rather than in one wrapped long line.
    """
    return mark_safe(adjlist.replace('\n', '<br/>'))

