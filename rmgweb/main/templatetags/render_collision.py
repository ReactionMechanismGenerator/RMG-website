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
Provides template tags for rendering collision parameters in various ways.
"""

# Register this module as a Django template tag library
from django import template
from django.utils.safestring import mark_safe

register = template.Library()
################################################################################


@register.filter
def render_collision_math(species, user=None):
    """
    Return a math representation of the given `species` collider parameters
    using MathJax. If a `user` is specified, the user's preferred units will be
    used; otherwise default units will be used.
    """

    result = ''

    result += '<table class="reference">\n'
    result += '<tr>'
    result += r'    <td class="label">Molecular weight:</td>'
    result += r'        <td>{0:.2f} g/mol</td>'.format(species.molecularWeight.value_si * 1000.)
    result += '</tr>\n'
    result += '<tr>'
    result += r'        <td class="label">Lennard-Jones sigma:</td>'
    result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(species.transportData.sigma.value, species.transportData.sigma.units)
    result += '</tr>\n'
    result += '<tr>'
    result += r'        <td class="label">Lennard-Jones epsilon:</td>'
    result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(species.transportData.epsilon.value, species.transportData.epsilon.units)
    result += '</tr>\n'
    result += '</table>\n'

    return mark_safe(result)
