from django import forms

class ReviewRequestForm(forms.Form):
    title = forms.CharField(max_length=255, required=True)
    filename = forms.CharField(max_length=255, required=False)
    code = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 20, "cols": 100}), required=True
    )
