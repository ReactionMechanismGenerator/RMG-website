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
from rmgpy.transport import *
from rmgpy.data.transport import *

################################################################################

@register.filter
def render_transport_math(transport, user=None):
    """
    Return a math representation of the given `transport` using MathJax. If a
    `user` is specified, the user's preferred units will be used; otherwise 
    default units will be used.
    """
    
    # The string that will be returned to the template
    result = ''
    
    if isinstance(transport, TransportData):
        
        result += '<table class="transportEntryData">\n'
        
        if transport.shapeIndex is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Shape Index</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(transport.shapeIndex, '')
            result += '</tr>\n'
        
        if transport.epsilon is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Epsilon</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(transport.epsilon.value, transport.epsilon.units)
            result += '</tr>\n'
            
        if transport.sigma is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Sigma</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(transport.sigma.value, transport.sigma.units)
            result += '</tr>\n'
            
        if transport.dipoleMoment is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Dipole Moment</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(transport.dipoleMoment.value, transport.dipoleMoment.units)
            result += '</tr>\n'
            
        if transport.polarizability is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Polarizability</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(transport.polarizability.value, transport.polarizability.units)
            result += '</tr>\n'  
            
        if transport.rotrelaxcollnum is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Rotational Relaxation Collision Number</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(transport.rotrelaxcollnum, '')
            result += '</tr>\n'   

        result += '</table>\n'
    
    elif isinstance(transport, CriticalPointGroupContribution):
         
#         All unitless, no need for or user inputted units or conversions. 
#         Tc = ''
#         Pc = ''
#         Vc = ''
#         Tb = ''
#         structureIndex = ''
                 
        result += '<table class="transportEntryData">\n'
         
        if transport.Tc is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Tc</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(transport.Tc, '')
            result += '</tr>\n'
         
        if transport.Pc is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Pc</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(transport.Pc, '')
            result += '</tr>\n'
             
        if transport.Vc is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Vc</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(transport.Vc, '')
            result += '</tr>\n'
             
        if transport.Tb is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Tb</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(transport.Tb, '')
            result += '</tr>\n'
             
        if transport.structureIndex is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Structure Index</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(transport.structureIndex, '')
            result += '</tr>\n'  
             
 
        result += '</table>\n'

    if isinstance(transport, (TransportData, CriticalPointGroupContribution)):
        result += '<table class="transportEntryData">'
#         if transport.Tmin is not None and transport.Tmax is not None:
#             result += '<tr><td class="key">Temperature range</td><td class="equals">=</td><td class="value">{0:g} to {1:g} {2!s}</td></tr>'.format(transport.Tmin.value_si, transport.Tmax.value_si, Tunits)
        result += '</table>'

    return mark_safe(result)



#def get_transport_data(transport, user=None):
#    Potentially a function for preparing the transport data for plotting
