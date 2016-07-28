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

from django import forms
from models import *
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe

class DivErrorList(ErrorList):
    def __unicode__(self):
        return self.as_divs()
    def as_divs(self):
        if not self: return u''
        return mark_safe(u'<label>&nbsp;</label>%s' % (''.join([u'<div class="error">%s</div>' % e for e in self])))

class UploadChemkinForm(forms.ModelForm):
    """
    A Django form for uploading a chemkin and RMG dictionary file.
    """
    class Meta:
        model = Chemkin
        fields = '__all__'

class ModelCompareForm(forms.ModelForm):
    """
    A Django form for comparing 2 RMG models using their chemkin and associated dictionary files.
    """
    class Meta:
        model = Diff
        fields = '__all__'
        
class UploadDictionaryForm(forms.ModelForm):
    """
    A Django form for uploading a RMG dictionary file.
    """
    class Meta:
        model = AdjlistConversion
        fields = '__all__'

class FluxDiagramForm(forms.ModelForm):
    """
    A Django form for creating a flux diagram by uploading the files required.
    """
    class Meta:
        model = FluxDiagram
        fields = '__all__'
        
class PopulateReactionsForm(forms.ModelForm):
    """
    A Django form for Populate Reactions when an input file is uploaded.  
    """
    class Meta:
        model = PopulateReactions
        fields = '__all__'

class UploadInputForm(forms.ModelForm):
    """
    A partial form which creates an Input model instance but only has a field for uploading the
    input.py file.
    """
    class Meta:
        model = Input
        fields = ('input_upload',)
        
        
class InputForm(forms.ModelForm):
    """
    Form for editing the conditions to be written in an input.py file for RMG-Py.
    """
    class Meta:
        model = Input
        exclude = ('input_upload',)
        widgets = {
            'maximumGrainSize': forms.TextInput(attrs={'size':'5'}),
            'minimumNumberOfGrains': forms.TextInput(attrs={'size':'5'}),
            'p_low': forms.TextInput(attrs={'size':'5'}),
            'p_high': forms.TextInput(attrs={'size':'5'}),
            'p_interp': forms.TextInput(attrs={'size':'2'}),
            'p_basis': forms.TextInput(attrs={'size':'2'}),
            'temp_low': forms.TextInput(attrs={'size':'5'}),
            'temp_high': forms.TextInput(attrs={'size':'5'}),
            'temp_interp': forms.TextInput(attrs={'size':'2'}),
            'temp_basis': forms.TextInput(attrs={'size':'2'}),
            'toleranceMoveToCore': forms.TextInput(attrs={'size':'3'}),
            'toleranceKeepInEdge': forms.TextInput(attrs={'size':'3'}),
            'toleranceInterruptSimulation': forms.TextInput(attrs={'size':'3'}),
            'maximumEdgeSpecies' : forms.TextInput(attrs={'size':'5'}),
            'minCoreSizeForPrune' : forms.TextInput(attrs={'size':'5'}),
            'minSpeciesExistIterationsForPrune' : forms.TextInput(attrs={'size':'3'}),
            'simulator_atol' : forms.TextInput(attrs={'size':'3'}),
            'simulator_rtol': forms.TextInput(attrs={'size':'3'}),
            'saveRestartPeriod':forms.TextInput(attrs={'size':'5'}),
            'maximumCarbonAtoms':forms.TextInput(attrs={'size':'2'}),
            'maximumOxygenAtoms':forms.TextInput(attrs={'size':'2'}),
            'maximumNitrogenAtoms':forms.TextInput(attrs={'size':'2'}),
            'maximumSiliconAtoms':forms.TextInput(attrs={'size':'2'}),
            'maximumSulfurAtoms':forms.TextInput(attrs={'size':'2'}),
            'maximumHeavyAtoms':forms.TextInput(attrs={'size':'2'}),
            'maximumRadicalElectrons':forms.TextInput(attrs={'size':'2'}),
            'maxRadicalNumber':forms.TextInput(attrs={'size':'2'}),
        }


class ThermoLibraryForm(forms.ModelForm):
    class Meta:
        model = ThermoLibrary
        fields = '__all__'

class ReactionLibraryForm(forms.ModelForm):
    class Meta:
        model= ReactionLibrary
        fields = '__all__'

class ReactorSpeciesForm(forms.ModelForm):
    class Meta:
        model = ReactorSpecies
        fields = '__all__'
        widgets ={
        'name': forms.TextInput(),
        'identifier': forms.TextInput(attrs={'onchange':'resolve(this.id);','class':'identifier'}),
        'adjlist':forms.Textarea(attrs={'cols': 50, 'rows': 10 }),
        'molefrac': forms.TextInput(attrs={'size':'5'}),
        }

    def clean_adjlist(self):
        """
        Custom validation for the adjlist field to ensure that a valid adjacency
        list has been provided.
        """
        try:
            adjlist = str(self.cleaned_data['adjlist'])
            if adjlist == '' : return ''
            molecule = Molecule()
            molecule.fromAdjacencyList(adjlist)
        except Exception, e:
            import traceback
            traceback.print_exc(e)
            raise forms.ValidationError('Invalid adjacency list.')
        return adjlist

class ReactorForm(forms.ModelForm):
    class Meta:
        model = Reactor
        fields = '__all__'
        widgets ={
            'temperature': forms.TextInput(attrs={'size':'5'}),
            'pressure': forms.TextInput(attrs={'size':'5'}),
            'terminationtime': forms.TextInput(attrs={'size':'5'}),
            'conversion': forms.TextInput(attrs={'size':'5'}),
        }
        
class NASAForm(forms.Form):
    """
    Form for entering a CHEMKIN format NASA polynomial
    """
    from rmgpy.chemkin import readThermoEntry
    NASA = forms.CharField(label="NASA Polynomial", widget = forms.Textarea(attrs={'cols': 100, 'rows': 10}), required=True)

    def clean_species(self):
            """
            Custom validation for the species field to ensure that a valid adjacency
            list has been provided.
            """
            try:
                NASA = str(self.cleaned_data['NASA'])
                if NASA == '' : return ''
                readThermoEntry(NASA)
            except Exception, e:
                import traceback
                traceback.print_exc(e)
                raise forms.ValidationError('Invalid NASA Polynomial.')
            return NASA
    