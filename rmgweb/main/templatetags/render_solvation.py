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
Provides template tags for rendering solvation  models in various ways.
"""

from django import template
from django.utils.safestring import mark_safe
from rmgpy.data.solvation import *

# Register this module as a Django template tag library
register = template.Library()

################################################################################


@register.filter
def render_solvation_math(solvation, user=None):
    """
    Return a math representation of the given `solvation` using MathJax. If a
    `user` is specified, the user's preferred units will be used; otherwise
    default units will be used.
    """
    # The string that will be returned to the template
    result = ''

    if isinstance(solvation, SoluteData):

        result += '<table class="solvationEntryData">\n'
        result += r'<td class = "key"><span>Abraham Parameters: </span></td>'

        if solvation.S is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>S</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.S, '')
            result += '</tr>\n'

        if solvation.B is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>B</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.B, '')
            result += '</tr>\n'

        if solvation.E is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>E</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.E, '')
            result += '</tr>\n'

        if solvation.L is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>L</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.L, '')

        if solvation.A is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>A</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.A, '')

        if solvation.V is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>V</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.V, '')
            result += '</tr>\n'

        result += '</table>\n'

    elif isinstance(solvation, SolventData):

        result += '<table class="solvationEntryData">\n'

        abraham_param_list = [(solvation.s_g, 's_g'),
                              (solvation.b_g, 'b_g'),
                              (solvation.e_g, 'e_g'),
                              (solvation.l_g, 'l_g'),
                              (solvation.a_g, 'a_g'),
                              (solvation.c_g, 'c_g')]

        result += r'<td class = "key"><span>Abraham Parameters (for solvation free energy): </span></td>'

        for param_value, param_name in abraham_param_list:
            result += '<tr>'
            result += r'    <td class = "key"><span>{0}</span></td>'.format(param_name)
            result += r'    <td class="equals">=</td>'
            if param_value is None:
                result += r'    <td class="value">N/A</td>'
            else:
                result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(
                    param_value, '')
            result += '</tr>\n'


        mintz_param_list = [(solvation.s_h, 's_h'),
                              (solvation.b_h, 'b_h'),
                              (solvation.e_h, 'e_h'),
                              (solvation.l_h, 'l_h'),
                              (solvation.a_h, 'a_h'),
                              (solvation.c_h, 'c_h')]

        result += r'<td class = "key"><span>Mintz Parameters (for solvation enthalpy): </span></td>'

        for param_value, param_name in mintz_param_list:
            result += '<tr>'
            result += r'    <td class = "key"><span>{0}</span></td>'.format(param_name)
            result += r'    <td class="equals">=</td>'
            if param_value is None:
                result += r'    <td class="value">N/A</td>'
            else:
                result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(
                    param_value, '')
            result += '</tr>\n'


        viscosity_param_list = [(solvation.A, 'A'),
                            (solvation.B, 'B'),
                            (solvation.C, 'C'),
                            (solvation.D, 'D'),
                            (solvation.E, 'E')]

        param_found_list = [value is not None for value, key in viscosity_param_list]

        result += r'<td class = "key"><span>Viscosity Parameters: </span></td>'

        result += '<tr>'
        result += r'    <td class = "key"><span>Solvent Viscosity μ at 298 K</span></td>'
        result += r'    <td class="equals">=</td>'
        if all(param_found_list):
            result += r'    <td class="value"><script type="math/tex">{0:.4f} \ \mathrm{{ {1!s} }} cP</script></td>'.format(solvation.get_solvent_viscosity(298)*1000, '')
        else:
            result += r'    <td class="value">N/A</td>'
        result += '</tr>\n'

        for param_value, param_name in viscosity_param_list:
            result += '<tr>'
            result += r'    <td class = "key"><span>{0}</span></td>'.format(param_name)
            result += r'    <td class="equals">=</td>'
            if param_value is None:
                result += r'    <td class="value">N/A</td>'
            else:
                result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(
                    param_value, '')
            result += '</tr>\n'


        solute_param_param_list = [(solvation.alpha, 'α'),
                            (solvation.beta, 'β')]

        result += r'<td class = "key"><span>Solute Parameters of Solvent: </span></td>'

        for param_value, param_name in solute_param_param_list:
            result += '<tr>'
            result += r'    <td class = "key"><span>{0}</span></td>'.format(param_name)
            result += r'    <td class="equals">=</td>'
            if param_value is None:
                result += r'    <td class="value">N/A</td>'
            else:
                result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(
                    param_value, '')
            result += '</tr>\n'


        result += r'<td class = "key"><span>Dielectric Constant: </span></td>'

        result += '<tr>'
        result += r'    <td class = "key"><script type="math/tex">ε</script></td>'
        result += r'    <td class="equals">=</td>'
        if solvation.eps is None:
            result += r'    <td class="value">N/A</td>'
        else:
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.eps, '')
        result += '</tr>\n'

        result += '</table>\n'

    elif isinstance(solvation, SolvationCorrection):

        if solvation.gibbs is not None:
            result += '<tr>'
            result += r'    <td class = "key"><script type="math/tex">\Delta G^{*}_{\rm solv}(298 {\rm K})</script></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.gibbs / 1000, 'kJ/mol')
            result += '</tr>\n'

        if solvation.enthalpy is not None:
            result += '<tr>'
            result += r'    <td class = "key"><script type="math/tex">\Delta H^{*}_{\rm solv}(298 {\rm K})</script></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.enthalpy / 1000, 'kJ/mol')
            result += '</tr>\n'

        if solvation.entropy is not None:
            result += '<tr>'
            result += r'    <td class = "key"><script type="math/tex">\Delta S^{*}_{\rm solv}(298 {\rm K})</script></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.4f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.entropy / 1000, 'kJ/mol/K')
            result += '</tr>\n'

        result += '</table>\n'

    elif isinstance(solvation, list) and len(solvation) == 3:

        if solvation[2] is not None: # temperature
            result += '<tr>'
            result += r'    <td class = "key"><span>Temperature</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation[2], 'K')
            result += '</tr>\n'

        if solvation[0] is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>VLE ratio </span><script type="math/tex">(y_{2}/x_{2})</script></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.3f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation[0], '')
            result += '</tr>\n'

        if solvation[1] is not None:
            result += '<tr>'
            result += r'    <td class = "key"><script type="math/tex">\Delta G^{*}_{\rm solv}(T)</script></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation[1] / 1000, 'kJ/mol')
            result += '</tr>\n'

        result += '</table>\n'

    if isinstance(solvation, (SoluteData, SolventData, SolvationCorrection)):
        result += '<table class="solvationEntryData">'
        result += '</table>'

    return mark_safe(result)
