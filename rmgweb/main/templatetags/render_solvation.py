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

        result += r'<td class = "key"><span>Mintz Parameters: </span></td>'

        if solvation.s_h is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>s_h</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.s_h, '')
            result += '</tr>\n'

        if solvation.b_h is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>b_h</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.b_h, '')
            result += '</tr>\n'

        if solvation.e_h is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>e_h</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.e_h, '')
            result += '</tr>\n'

        if solvation.l_h is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>l_h</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.l_h, '')
            result += '</tr>\n'

        if solvation.a_h is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>a_h</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.a_h, '')
            result += '</tr>\n'

        if solvation.c_h is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>c_h</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.c_h, '')
            result += '</tr>\n'

        result += r'<td class = "key"><span>Abraham Parameters: </span></td>'

        if solvation.s_g is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>s_g</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.s_g, '')
            result += '</tr>\n'

        if solvation.b_g is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>b_g</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.b_g, '')
            result += '</tr>\n'

        if solvation.e_g is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>e_g</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.e_g, '')
            result += '</tr>\n'

        if solvation.l_g is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>l_g</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.l_g, '')
            result += '</tr>\n'

        if solvation.a_g is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>a_g</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.a_g, '')
            result += '</tr>\n'

        if solvation.c_g is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>c_g</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.c_g, '')
            result += '</tr>\n'

        result += r'<td class = "key"><span>Viscosity Parameters: </span></td>'

        result += '<tr>'
        result += r'    <td class = "key"><span>Solvent Viscosity μ at 298 K</span></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }} cP</script></td>'.format(solvation.get_solvent_viscosity(298)*1000, '')
        result += '</tr>\n'

        if solvation.A is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>A</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.A, '')
            result += '</tr>\n'

        if solvation.B is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>B</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.B, '')
            result += '</tr>\n'

        if solvation.C is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>C</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.C, '')
            result += '</tr>\n'

        if solvation.D is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>D</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.D, '')
            result += '</tr>\n'

        if solvation.E is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>E</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.E, '')
            result += '</tr>\n'

        result += r'<td class = "key"><span>Solute Parameters of Solvent: </span></td>'

        if solvation.alpha is not None:
            result += '<tr>'
            result += r'    <td class = "key"><script type="math/tex">α</script></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.alpha, '')
            result += '</tr>\n'

        if solvation.beta is not None:
            result += '<tr>'
            result += r'    <td class = "key"><script type="math/tex">β</script></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.beta, '')
            result += '</tr>\n'

        result += r'<td class = "key"><span>Dielectric Constant: </span></td>'

        if solvation.eps is not None:
            result += '<tr>'
            result += r'    <td class = "key"><script type="math/tex">ε</script></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.eps, '')
            result += '</tr>\n'

        result += '</table>\n'

    elif isinstance(solvation, SolvationCorrection):

        if solvation.gibbs is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Gibbs Free Energy of Solvation</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.gibbs / 1000, 'kJ/mol')
            result += '</tr>\n'

        if solvation.enthalpy is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Enthalpy of Solvation</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.enthalpy / 1000, 'kJ/mol')
            result += '</tr>\n'

        if solvation.entropy is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Entropy of Solvation</span></td>'
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
            result += r'    <td class = "key"><span>Vapor-Liquid Equilibrium Ratio of a Solute (y2/x2)</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.3f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation[0], '')
            result += '</tr>\n'

        if solvation[1] is not None:
            result += '<tr>'
            result += r'    <td class = "key"><span>Gibbs Free Energy of Solvation</span></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation[1] / 1000, 'kJ/mol')
            result += '</tr>\n'

        result += '</table>\n'

    if isinstance(solvation, (SoluteData, SolventData, SolvationCorrection)):
        result += '<table class="solvationEntryData">'
        result += '</table>'

    return mark_safe(result)
