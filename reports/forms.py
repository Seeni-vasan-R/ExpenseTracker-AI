from django import forms


class ReportFilterForm(forms.Form):

    FILTER_CHOICES = [
        ("today", "Today"),
        ("week", "Last 7 Days"),
        ("month", "This Month"),
        ("year", "This Year"),
        ("custom", "Custom Range"),
    ]

    filter_type = forms.ChoiceField(
        choices=FILTER_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )

    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )