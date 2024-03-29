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
from rmgpy.data.base import Entry
from rmgpy.species import Species
from rmgpy.molecule.group import Group
from rmgpy.data.solvation import *

# Register this module as a Django template tag library
register = template.Library()

################################################################################


def print_param_list(param_list, result, decimal_place=2, unit=''):
    """
    Return a result string with parameter data appended. The input `param_list` is a list of a tuple
    (param_value, param_name), where `param_value` is a float and `param_name` is a string. If `param_value`
    is None, it writes 'N/A'.
    """
    for param_value, param_name in param_list:
        result += '<tr>'
        result += r'    <td class = "key"><span>{0}</span></td>'.format(param_name)
        result += r'    <td class="equals">=</td>'
        if param_value is None:
            result += r'    <td class="value">N/A</td>'
        else:
            param_value = '%.*f' % (decimal_place, param_value)
            result += r'    <td class="value"><script type="math/tex">{0} \ \mathrm{{ {1!s} }}</script></td>'.format(
                param_value, unit)
        result += '</tr>\n'
    return result


@register.filter
def render_solvation_math(solvation, user=None):
    """
    Return a math representation of the given `solvation` using MathJax. If a
    `user` is specified, the user's preferred units will be used; otherwise
    default units will be used.
    """
    # The string that will be returned to the template
    result = ''

    if isinstance(solvation, Entry):
        data = solvation.data
        data_count = solvation.data_count

        if isinstance(data, SoluteData):
            result += '<table class="solvationEntryData">\n'
            result += r'<td class = "key"><span>Abraham Parameters: </span></td>'

            solute_param_list = [(data.S, 'S'),
                                  (data.B, 'B'),
                                  (data.E, 'E'),
                                  (data.L, 'L'),
                                  (data.A, 'A'),
                                  (data.V, 'V')]

            decimal_place = 2
            # Use more decimal places and remove V for Group object because V does not need the group value.
            if isinstance(solvation.item, Group):
                decimal_place = 5
                solute_param_list = solute_param_list[:-1]

            result = print_param_list(solute_param_list, result, decimal_place=decimal_place)

            if data_count is not None:
                result += r'<td class = "key"><span>Number of Data Used to Fit Each Group Value: </span></td>'

                data_count_list = [(data_count.S, 'S'),
                                   (data_count.B, 'B'),
                                   (data_count.E, 'E'),
                                   (data_count.L, 'L'),
                                   (data_count.A, 'A')]

                result = print_param_list(data_count_list, result, decimal_place=0)

            result += '</table>\n'

        elif isinstance(data, SolventData):
            result += '<table class="solvationEntryData">\n'

            abraham_param_list = [(data.s_g, 's_g'),
                                  (data.b_g, 'b_g'),
                                  (data.e_g, 'e_g'),
                                  (data.l_g, 'l_g'),
                                  (data.a_g, 'a_g'),
                                  (data.c_g, 'c_g')]

            param_found_list = [value is not None for value, key in abraham_param_list]

            result += r'<td class = "key"><span>Abraham Parameters (for solvation free energy): </span></td>'
            if any(param_found_list):
                result = print_param_list(abraham_param_list, result, decimal_place=5)
            else:
                result += r'<td class="value">not available</td>'

            if data_count is not None and data_count.dGsolvCount is not None and data_count.dGsolvMAE is not None:
                data_count_list = [(data_count.dGsolvCount, 'Number of Data Used to Fit the Abraham Parameters')]
                result = print_param_list(data_count_list, result, decimal_place=0)
                data_count_list = [(data_count.dGsolvMAE[0], 'Associated Solvation Free Energy Mean Absolute Error')]
                result = print_param_list(data_count_list, result, decimal_place=2, unit='kcal/mol')
            result += r'<tr><td style="line-height:20px;" colspan=3>&nbsp;</td></tr>' # add an empty line to make it look nicer


            mintz_param_list = [(data.s_h, 's_h'),
                                (data.b_h, 'b_h'),
                                (data.e_h, 'e_h'),
                                (data.l_h, 'l_h'),
                                (data.a_h, 'a_h'),
                                (data.c_h, 'c_h')]

            param_found_list = [value is not None for value, key in mintz_param_list]

            result += r'<td class = "key"><span>Mintz Parameters (for solvation enthalpy): </span></td>'
            if any(param_found_list):
                result = print_param_list(mintz_param_list, result, decimal_place=5)
            else:
                result += r'<td class="value">not available</td>'

            if data_count is not None and data_count.dHsolvCount is not None and data_count.dHsolvMAE is not None:
                data_count_list = [(data_count.dHsolvCount, 'Number of Data Used to Fit the Mintz Parameters')]
                result = print_param_list(data_count_list, result, decimal_place=0)
                data_count_list = [(data_count.dHsolvMAE[0], 'Associated Solvation Enthalpy Mean Absolute Error')]
                result = print_param_list(data_count_list, result, decimal_place=2, unit='kcal/mol')
            result += r'<tr><td style="line-height:20px;" colspan=3>&nbsp;</td></tr>' # add an empty line to make it look nicer


            viscosity_param_list = [(data.A, 'A'),
                                    (data.B, 'B'),
                                    (data.C, 'C'),
                                    (data.D, 'D'),
                                    (data.E, 'E')]

            param_found_list = [value is not None for value, key in viscosity_param_list]

            result += r'<td class = "key"><span>Viscosity Parameters: </span></td>'
            if any(param_found_list):
                result += '<tr>'
                result += r'    <td class = "key"><span>Solvent Viscosity μ at 298 K</span></td>'
                result += r'    <td class="equals">=</td>'
                if all(param_found_list):
                    result += r'    <td class="value"><script type="math/tex">{0:.4f} \ \mathrm{{ {1!s} }} cP</script></td>'.format(
                        data.get_solvent_viscosity(298) * 1000, '')
                else:
                    result += r'    <td class="value">N/A</td>'
                result += '</tr>\n'

                result = print_param_list(viscosity_param_list, result, decimal_place=2)
            else:
                result += r'<td class="value">not available</td>'
            result += r'<tr><td style="line-height:20px;" colspan=3>&nbsp;</td></tr>' # add an empty line to make it look nicer


            solvent_solute_param_list = [(data.alpha, 'α'),
                                       (data.beta, 'β')]

            result += r'<td class = "key"><span>Solute Parameters of Solvent: </span></td>'

            result = print_param_list(solvent_solute_param_list, result, decimal_place=2)

            result += r'<td class = "key"><span>Dielectric Constant: </span></td>'

            result += '<tr>'
            result += r'    <td class = "key"><script type="math/tex">ε</script></td>'
            result += r'    <td class="equals">=</td>'
            if data.eps is None:
                result += r'    <td class="value">N/A</td>'
            else:
                result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(
                    data.eps, '')
            result += '</tr>\n'

            result += '</table>\n'

    else:

        if isinstance(solvation, SoluteData):
            result += '<table class="solvationEntryData">\n'
            result += r'<td class = "key"><span>Abraham Parameters: </span></td>'

            solute_param_list = [(solvation.S, 'S'),
                                  (solvation.B, 'B'),
                                  (solvation.E, 'E'),
                                  (solvation.L, 'L'),
                                  (solvation.A, 'A'),
                                  (solvation.V, 'V')]

            result = print_param_list(solute_param_list, result, decimal_place=5)
            result += '</table>\n'

        elif isinstance(solvation, list) and solvation[0] == 'Link':
            result += r'<p>This group uses the group values of '
            result += r'<a href="{0}"> {1} </a>'.format(solvation[1], solvation[2])
            result += '</p>'

        elif solvation is None:
            result += r'<p>This group is one of the top nodes or general parent groups that do not need the group values.</p>'

        elif isinstance(solvation, SolvationCorrection):

            result += '<tr>'
            result += r'    <td class = "key"><script type="math/tex">\Delta G^{*}_{\rm solv}(298 {\rm K})</script></td>'
            result += r'    <td class="equals">=</td>'
            if solvation.gibbs is not None:
                result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.gibbs / 1000, 'kJ/mol')
            else:
                result += r'    <td class="value">N/A</td>'
            result += '</tr>\n'

            result += '<tr>'
            result += r'    <td class = "key"><script type="math/tex">\Delta H^{*}_{\rm solv}(298 {\rm K})</script></td>'
            result += r'    <td class="equals">=</td>'
            if solvation.enthalpy is not None:
                result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.enthalpy / 1000, 'kJ/mol')
            else:
                result += r'    <td class="value">N/A</td>'
            result += '</tr>\n'

            result += '<tr>'
            result += r'    <td class = "key"><script type="math/tex">\Delta S^{*}_{\rm solv}(298 {\rm K})</script></td>'
            result += r'    <td class="equals">=</td>'
            if solvation.entropy is not None:
                result += r'    <td class="value"><script type="math/tex">{0:.4f} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation.entropy / 1000, 'kJ/mol/K')
            else:
                result += r'    <td class="value">N/A</td>'
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
                result += r'    <td class="value"><script type="math/tex">{0:.3e} \ \mathrm{{ {1!s} }}</script></td>'.format(solvation[0], '')
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

@register.filter
def render_solvation_molecule(item, solvent_search_result=False):
    """
    Return a SMILES string(s) of the given `item`, which is either an instance of `Species` or
    a list of an instance of `Species`.
    """
    # The string that will be returned to the template
    result = ''
    # Case 1. Solvent - this is given as a list of Species objects.
    if isinstance(item, list):
        if solvent_search_result:
            result += r'<p>&emsp;&emsp;Result solvent SMILES: &nbsp;'
        else:
            result += r'<h2>Molecule SMILES</h2>' + '\n'
            result += r'<p>'
        if len(item) == 1:
            result += item[0].smiles
        else:
            for spc in item:
                result += f'{spc.smiles}, '
            result = result[:-2]
            result += ' (mixture solvents) '
        result += r'</p>'
    # Case 2. Solute - this is given as a Specie object.
    elif isinstance(item, Species):
        result += r'<h2>Molecule SMILES</h2>' + '\n'
        result += r'<p>'
        result += item.smiles
        result += r'</p>'
    # Case 3. Solvation solute group - this is given as a Group object
    elif isinstance(item, Group):
        result += r'<h2>Group Adjacency List</h2>' + '\n'
        result += r'<p><pre>'
        result += item.to_adjacency_list()
        result += r'</pre></p>'
    return mark_safe(result)


@register.filter
def render_smiles_list(smiles_list):
    """
    Format and return a SMILES string(s).
    """
    # The string that will be returned to the template
    result = r'<h3>Solvent SMILES:</h3>' + '\n'
    result += r'<p>'
    if len(smiles_list) == 1:
        result += smiles_list[0]
    else:
        result += 'This is a mixture of the following solvents: '
        for smiles in smiles_list:
            result += f'{smiles}, '
        result = result[:-2]
    result += r'</p>'
    return mark_safe(result)


@register.filter
def get_items(dictionary, key):
    '''
    By default, Django does not let the user lookup a dictionary value if the key is the loop variable.
    This filter is a workaround to enable using loop variable as a key in a view.
    '''
    return dictionary.get(key)
