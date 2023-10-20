from django import forms

class DriveUploadForm(forms.Form):
    file = forms.FileField(required=False)
    area = forms.TextInput()
    city = forms.TextInput()
    name = forms.TextInput()
    dir_name = forms.TextInput()

class ProposalUploadForm(forms.Form):
    proposalFile = forms.FileField(required=False)
    year = forms.TextInput()
    area = forms.TextInput()
    city = forms.TextInput()
    school = forms.TextInput()