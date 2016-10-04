"""
Forms for FOIA Machine
"""

from django import forms

from autocomplete_light import shortcuts as autocomplete_light

from muckrock.foiamachine.models import FoiaMachineRequest, FoiaMachineCommunication

class FoiaMachineRequestForm(autocomplete_light.ModelForm):
    """The FOIA Machine Request form provides a basis for creating and updating requests."""
    class Meta:
        model = FoiaMachineRequest
        fields = ['title', 'request_language', 'jurisdiction', 'agency']
        autocomplete_names = {
            'jurisdiction': 'JurisdictionAutocomplete',
            'agency': 'AgencyAutocomplete',
        }
        labels = {
            'request_language': 'Request',
        }

    def clean(self):
        cleaned_data = super(FoiaMachineRequestForm, self).clean()
        jurisdiction = cleaned_data.get('jurisdiction')
        agency = cleaned_data.get('agency')
        if agency and agency.jurisdiction != jurisdiction:
            raise forms.ValidationError('This agency does not belong to the jurisdiction.')
        return cleaned_data


class FoiaMachineCommunicationForm(forms.ModelForm):
    """The FOIA Machine Communication form allows for creating and updating communications."""
    class Meta:
        model = FoiaMachineCommunication
        fields = ['request', 'sender', 'receiver', 'message', 'received',]
        widgets = {
            'request': forms.HiddenInput(),
        }
        help_texts = {
            'sender': 'What is the name or email of who sent the message?',
            'receiver': 'What is the name or email of who the message was sent to?',
            'received': 'Was this message sent to you?'
        }
