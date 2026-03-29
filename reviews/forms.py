from django import forms
from reviews.models import ReviewRequest


# class ReviewRequestForm(forms.ModelForm):
#     class Meta:
#         model = ReviewRequest
#         fields = ["title", "filename", "code"]
#         widget = (
#             {
#                 "title": forms.TextInput(attrs={"placeholder": "Title of MR"}),
#                 "filename": forms.TextInput(attrs={"placeholder": "eg: Card.tsx"}),
#                 "code": forms.Textarea(
#                     attrs={
#                         "placeholder": "Paste your react/react native code here",
#                         "rows": 20,
#                     }
#                 ),
#             },
#         )


class ReviewRequestForm(forms.Form):
    title = forms.CharField(max_length=255, required=True)
    filename = forms.CharField(max_length=255, required=False)
    code = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 20, "cols": 100}), required=True
    )
