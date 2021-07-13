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

import copy
import sys

import rmgpy
from django import forms
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe
from rmgpy.molecule.molecule import Molecule
from rmgweb.database.tools import database


class DivErrorList(ErrorList):
    def __str__(self):
        return self.as_divs()

    def as_divs(self):
        if not self:
            return ''
        return mark_safe('<div>%s</div>' % (''.join(['<div class="error">%s</div>' % e for e in self])))


class ThermoSearchForm(forms.Form):
    """
    This form provides a means of specifying a species to get thermodynamic
    data for.
    """
    species = forms.CharField(widget=forms.widgets.Textarea(attrs={'rows': 6, 'cols': 30}))

    def clean_species(self):
        """
        Custom validation for the species field to ensure that a valid adjacency
        list has been provided.
        """
        try:
            molecule = Molecule()
            molecule.from_adjacency_list(self.cleaned_data['species'])
        except Exception:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('Invalid adjacency list.')
        return self.cleaned_data['species']

    def as_table(self):
        "Returns this form rendered as HTML <tr>s -- excluding the <table></table>."
        return self._html_output(
            normal_row='<tr%(html_class_attr)s><th>%(label)s</th><td>%(errors)s%(field)s%(help_text)s</td></tr>',
            error_row='<tr><td colspan="2">%s</td></tr>',
            row_ender='</td></tr>',
            help_text_html='<br />%s',
            errors_on_separate_row=False)


class KineticsSearchForm(forms.Form):
    """
    This form provides a means of specifying a set of reactants to get
    kinetic data for.
    """
    reactant1_identifier = forms.CharField(label="Reactant #1 Identifier", widget=forms.TextInput(attrs={'onchange': 'resolve("reactant1");', 'class': 'identifier'}), required=False)
    reactant1 = forms.CharField(label="Reactant #1", widget=forms.widgets.Textarea(attrs={'rows': 6, 'cols': 30}))
    reactant2_identifier = forms.CharField(label="Reactant #2 Identifier", widget=forms.TextInput(attrs={'onchange': 'resolve("reactant2");', 'class': 'identifier'}), required=False)
    reactant2 = forms.CharField(label="Reactant #2", widget=forms.widgets.Textarea(attrs={'rows': 6, 'cols': 30}), required=False)
    product1_identifier = forms.CharField(label="Product #1 Identifier", widget=forms.TextInput(attrs={'onchange': 'resolve("product1");', 'class': 'identifier'}), required=False)
    product1 = forms.CharField(label="Product #1", widget=forms.widgets.Textarea(attrs={'rows': 6, 'cols': 30}), required=False)
    product2_identifier = forms.CharField(label="Product #2 Identifier", widget=forms.TextInput(attrs={'onchange': 'resolve("product2");', 'class': 'identifier'}), required=False)
    product2 = forms.CharField(label="Product #2", widget=forms.widgets.Textarea(attrs={'rows': 6, 'cols': 30}), required=False)
    resonance = forms.BooleanField(label="Generate Resonance Structures", widget=forms.CheckboxInput(), initial=True, required=False)

    def clean_reactant1(self):
        """
        Custom validation for the reactant1 field to ensure that a valid
        adjacency list has been provided.
        """
        try:
            molecule = Molecule()
            molecule.from_adjacency_list(self.cleaned_data['reactant1'])
        except Exception:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('Invalid adjacency list.')
        return self.cleaned_data['reactant1']

    def clean_reactant2(self):
        """
        Custom validation for the reactant1 field to ensure that a valid
        adjacency list has been provided.
        """
        try:
            adjlist = self.cleaned_data['reactant2']
            if adjlist.strip() == '':
                return ''
            molecule = Molecule()
            molecule.from_adjacency_list(adjlist)
        except Exception:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('Invalid adjacency list.')
        return self.cleaned_data['reactant2']

    def clean_product1(self):
        """
        Custom validation for the product1 field to ensure that a valid
        adjacency list has been provided.
        """
        try:
            adjlist = self.cleaned_data['product1']
            if adjlist.strip() == '':
                return ''
            molecule = Molecule()
            molecule.from_adjacency_list(adjlist)
        except Exception:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('Invalid adjacency list.')
        return self.cleaned_data['product1']

    def clean_product2(self):
        """
        Custom validation for the product1 field to ensure that a valid
        adjacency list has been provided.
        """
        try:
            adjlist = self.cleaned_data['product2']
            if adjlist.strip() == '':
                return ''
            molecule = Molecule()
            molecule.from_adjacency_list(adjlist)
        except Exception:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('Invalid adjacency list.')
        return self.cleaned_data['product2']


class MoleculeSearchForm(forms.Form):
    """
    Form for drawing molecule from adjacency list
    """
    species_identifier = forms.CharField(
        label="Species Identifier",
        widget=forms.TextInput(attrs={'onchange': 'resolve();', 'style': 'width:100%;'}),
        required=False)
    species = forms.CharField(
        label="Adjacency List",
        widget=forms.Textarea(attrs={'cols': 50, 'rows': 20, 'onchange': "$('.result').hide();"}),
        required=True)

    def clean_species(self):
        """
        Custom validation for the species field to ensure that a valid adjacency
        list has been provided.
        """
        try:
            adjlist = self.cleaned_data['species']
            if adjlist == '':
                return ''
            molecule = Molecule()
            molecule.from_adjacency_list(adjlist)
        except Exception:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('Invalid adjacency list.')
        return adjlist


class SolvationSearchForm(forms.ModelForm):
    """
    Form for searching for solvation properties between a solute and a solvent.
    """
    class Meta(object):

        from rmgweb.database.models import SolventSelection
        model = SolventSelection
        fields = '__all__'
        widgets = {'species_identifier': forms.TextInput(
            attrs={'onchange': 'resolve("adjlist");', 'class': 'identifier', 'style': 'width:100%;'}
            ),
            'adjlist': forms.Textarea(attrs={'cols': 50, 'rows': 10}),
        }

    def clean_adjlist(self):
        """
        Custom validation for the adjlist field to ensure that a valid adjacency
        list has been provided.
        """
        try:
            adjlist = self.cleaned_data['adjlist']
            if adjlist == '':
                return ''
            molecule = Molecule()
            molecule.from_adjacency_list(adjlist)
        except Exception:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('Invalid adjacency list.')
        return adjlist

    def clean_temp(self):
        """
        Custom validation for the temperature field to ensure that a valid temperature has been provided
        """
        temp = self.cleaned_data['temp']
        try:
            temp = float(temp)
        except:
            raise forms.ValidationError('Only non-empty numeric input is allowed')
        database.load('solvation')
        db = database.get_solvation_database('', '')
        solvent_temp = self.cleaned_data['solvent_temp']
        if not solvent_temp == '':
            Tc = db.get_solvent_data(solvent_temp).get_solvent_critical_temperature()
            if temp < 280 or temp >= Tc:
                raise forms.ValidationError('Temperature is out of the valid range')
        return temp


class SolvationSearchMLForm(forms.ModelForm):
    """
    Form for searching for the solvation properties for a given solvent-solute pair(s) using an ML model.
    """
    class Meta(object):

        from rmgweb.database.models import SolvationSearchML
        model = SolvationSearchML
        fields = '__all__'
        widgets = {'solvent_solute_smiles': forms.Textarea(attrs={'cols': 80, 'rows': 10,
                                                            'placeholder': "solventSMILES_soluteSMILES \n"
                                                                           "CC#N_CCCC \nO_CCO \nO_C1=CC=CC=C1 ..."}),
        }

    def clean_solvent_solute_smiles(self):
        """
        Custom validation for the solute_smiles_list field to ensure that the number of solute SMILES
        does not exceed 100.
        """
        solvent_solute_smiles = self.cleaned_data['solvent_solute_smiles']
        solvent_solute_smiles_list = solvent_solute_smiles.split()
        if len(solvent_solute_smiles_list) > 200:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('The number of input solvent-solute pairs cannot exceed 200.')
        return solvent_solute_smiles

    def clean_option_selected(self):
        """
        Custom validation for the option_selected to ensure at least one calculation option is selected.
        """
        calc_dGsolv = self.cleaned_data['calc_dGsolv']
        calc_dHsolv = self.cleaned_data['calc_dHsolv']
        calc_dSsolv = self.cleaned_data['calc_dSsolv']
        calc_logK = self.cleaned_data['calc_logK']
        calc_logP = self.cleaned_data['calc_logP']

        option_selected = any([calc_dGsolv, calc_dHsolv, calc_dSsolv, calc_logK, calc_logP])

        if option_selected is False:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('At least one option must be selected.')
        return option_selected


class SolvationSearchTempDepForm(forms.ModelForm):
    """
    Form for searching for temperature-dependent solvation properties for a given solvent-solute pair(s) at a
    an input temperature(s).
    """
    class Meta(object):

        from rmgweb.database.models import SolvationSearchTempDep
        model = SolvationSearchTempDep
        fields = '__all__'
        widgets = {'solvent_solute_temp': forms.Textarea(attrs={'cols': 80, 'rows': 10,
                                                                'placeholder': "solventSMILES_soluteSMILES_Temperature \n"
                                                                               "CCO_CCCCCCCC_298 \nO_CCCO_300 \nC1CCCCC1_C1=CC=CC=C1_400 ..."}),
        }

    def clean_solvent_solute_temp(self):
        """
        Custom validation for the solvent_solute_temp field to ensure that the number of solvent-solute-temperature
        pairs do not exceed 200.
        """
        solvent_solute_temp = self.cleaned_data['solvent_solute_temp']
        solvent_solute_temp_list = solvent_solute_temp.split()
        if len(solvent_solute_temp_list) > 200:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('The number of solvent-solute-temperature inputs cannot exceed 200.')
        return solvent_solute_temp

    def clean_option_selected(self):
        """
        Custom validation for the option_selected to ensure at least one calculation option is selected.
        """
        calc_dGsolv = self.cleaned_data['calc_dGsolv']
        calc_Kfactor = self.cleaned_data['calc_Kfactor']
        calc_henry = self.cleaned_data['calc_henry']
        calc_logK = self.cleaned_data['calc_logK']
        calc_logP = self.cleaned_data['calc_logP']

        option_selected = any([calc_dGsolv, calc_Kfactor, calc_henry, calc_logK, calc_logP])

        if option_selected is False:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('At least one option must be selected.')
        return option_selected


class SoluteSearchForm(forms.ModelForm):
    """
    Form for searching for the Abraham solute parameters for a solute species and optionally search for
    solvation properties if a solvent species is also chosen.
    """
    class Meta(object):

        from rmgweb.database.models import SoluteSearch
        model = SoluteSearch
        fields = '__all__'
        widgets = {'solute_smiles': forms.Textarea(attrs={'cols': 50, 'rows': 10,
                                                            'placeholder': "CCCC CCO C1=CC=CC=C1 ..."}),
        }

    def clean_solute_smiles(self):
        """
        Custom validation for the solute_smiles_list field to ensure that the number of solute SMILES
        does not exceed 100.
        """
        solute_smiles = self.cleaned_data['solute_smiles']
        solute_smiles_list = solute_smiles.split()
        if len(solute_smiles_list) > 100:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('The number of input solute SMILESs cannot exceed 100.')
        return solute_smiles

    def clean_solute_estimator(self):
        """
        Custom validation for the solute_estimator field to ensure that the user select a method for solute parameter
        estimation.
        """
        solute_estimator = self.cleaned_data['solute_estimator']
        if solute_estimator == '':
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('You must select an estimation method for the solute parameters.')
        return solute_estimator


class SolventSearchForm(forms.ModelForm):
    """
    Form for searching for solvent data.
    """
    class Meta(object):

        from rmgweb.database.models import SolventSelection
        model = SolventSelection
        fields = '__all__'
        widgets = {'species_identifier': forms.TextInput(
            attrs={'onchange': 'resolve("adjlist");', 'class': 'identifier', 'style': 'width:100%;'}
            ),
            'adjlist': forms.Textarea(attrs={'cols': 50, 'rows': 10}),
        }

    def clean_adjlist(self):
        """
        Custom validation for the adjlist field to ensure that a valid adjacency
        list has been provided.
        """
        try:
            adjlist = self.cleaned_data['adjlist']
            if adjlist == '':
                return ''
            molecule = Molecule()
            molecule.from_adjacency_list(adjlist)
        except Exception:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('Invalid adjacency list.')
        return adjlist


class GroupDrawForm(forms.Form):
    """
    Form for drawing group from adjacency list
    """
    group = forms.CharField(
        label="Adjacency List",
        widget=forms.Textarea(attrs={'cols': 50, 'rows': 20, 'onchange': "$('.result').hide();"}),
        required=True)

    def clean_group(self):
        """
        Custom validation for the species field to ensure that a valid adjacency
        list has been provided.
        """
        from rmgpy.molecule import Group
        try:
            adjlist = self.cleaned_data['group']
            if adjlist == '':
                return ''
            group = Group()
            group.from_adjacency_list(self.cleaned_data['group'])
        except Exception:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('Invalid adjacency list.')
        return adjlist


class EniSearchForm(forms.Form):
    """
    Form for drawing molecule from adjacency list
    """
    detergent_identifier = forms.CharField(
        label="Detergent Identifier",
        widget=forms.TextInput(attrs={'onchange': 'resolve("detergent");', 'class': 'identifier'}),
        required=False)
    detergent = forms.CharField(
        label="Detergent",
        widget=forms.widgets.Textarea(attrs={'rows': 6, 'cols': 30}))
    deposit_identifier = forms.CharField(
        label="Deposit Identifier",
        widget=forms.TextInput(attrs={'onchange': 'resolve("deposit");', 'class': 'identifier'}),
        required=False)
    deposit = forms.CharField(
        label="Deposit",
        widget=forms.widgets.Textarea(attrs={'rows': 6, 'cols': 30}),
        required=False)

    def clean_detergent(self):
        """
        Return molecular representation of input detergent structure
        """
        try:
            detergent = Molecule()
            detergent.from_adjacency_list(self.cleaned_data['detergent'])
        except Exception:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('Invalid SMILES entry.')
        return self.cleaned_data['detergent']

    def clean_deposit(self):
        """
        Return molecular representation of input deposit structure
        """
        try:
            deposit = Molecule()
            deposit.from_adjacency_list(self.cleaned_data['deposit'])
        except Exception:
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('Invalid SMILES entry.')
        return self.cleaned_data['deposit']


class ThermoEntryEditForm(forms.Form):
    """
    Form for editing thermo database entries
    """
    entry = forms.CharField(
        label="Database Entry",
        widget=forms.Textarea(attrs={'cols': 80, 'rows': 40, 'class': 'data_entry'}),
        required=True)
    change = forms.CharField(
        label="Summary of changes",
        widget=forms.TextInput(attrs={'class': 'change_summary'}),
        required=True)

    def clean_entry(self):
        """
        Custom validation for the entry field to ensure that a valid
        entry has been provided.
        """
        new_database = rmgpy.data.thermo.ThermoDatabase()
        new_depository = rmgpy.data.thermo.ThermoDepository()
        global_context = {'__builtins__': None}  # disable even builtins
        local_context = copy.copy(new_database.local_context)
        local_context['entry'] = new_depository.load_entry
        for key, value in rmgpy.data.base.Database.local_context.items():
            local_context[key] = value

        entry_string = self.cleaned_data['entry']
        try:
            entry = eval("entry( index=-1, {0})".format(entry_string), global_context, local_context)
        except Exception:
            print("Invalid entry from ThermoEntryEditForm.")
            print(repr(entry_string))
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('Invalid entry.' + sys.exc_info()[1])
        return entry


class KineticsEntryEditForm(forms.Form):
    """
    Form for editing kinetics database entries
    """
    entry = forms.CharField(
        label="Database Entry",
        widget=forms.Textarea(attrs={'cols': 80, 'rows': 40, 'class': 'data_entry'}),
        required=True)
    change = forms.CharField(
        label="Summary of changes",
        widget=forms.TextInput(attrs={'class': 'change_summary'}),
        required=True)

    def clean_entry(self):
        """
        Custom validation for the entry field to ensure that a valid
        entry has been provided.
        """
        new_database = rmgpy.data.kinetics.KineticsDatabase()
        new_depository = rmgpy.data.kinetics.KineticsDepository()
        global_context = {'__builtins__': None}  # disable even builtins
        local_context = copy.copy(new_database.local_context)
        local_context['entry'] = new_depository.load_entry
        for key, value in rmgpy.data.base.Database.local_context.items():
            local_context[key] = value

        entry_string = self.cleaned_data['entry']
        try:
            entry = eval("entry( index=-1, {0})".format(entry_string), global_context, local_context)
        except Exception:
            print("Invalid entry from KineticsEntryEditForm.")
            print(repr(entry_string))
            import traceback
            traceback.print_exc()
            raise forms.ValidationError('Invalid entry.' + sys.exc_info()[1])
        return entry


class RateEvaluationForm(forms.Form):
    """
    This form allows the user to enter a specific temperature and pressure and display the resulting rates
    on a set of kinetics.
    """
    # hidden = forms.CharField(widget=forms.HiddenInput())
    temp_units = (('K', 'K',),)
    p_units = (('bar', 'bar',), ('torr', 'torr',), ('atm', 'atm',))
    temperature = forms.FloatField(label="Temperature")
    temperature_units = forms.ChoiceField(choices=temp_units)
    pressure = forms.FloatField(label="Pressure")
    pressure_units = forms.ChoiceField(choices=p_units)
