#refer to https://github.com/stefanfoulis/django-phonenumber-field/issues/202
from phonenumber_field.widgets import (
    PhonePrefixSelect, Select, translation, settings,
    _COUNTRY_CODE_TO_REGION_CODE, Locale, TextInput, PhoneNumber, MultiWidget,
)

class CustomPhonePrefixSelect(PhonePrefixSelect):
    initial = None

    def __init__(self, initial=None):
        choices = [("", "---------")]
        language = translation.get_language() or settings.LANGUAGE_CODE
        if language:
            locale = Locale(translation.to_locale(language))
            for prefix, values in _COUNTRY_CODE_TO_REGION_CODE.items():
                prefix = "+%d" % prefix
                # if initial and initial in values:
                #     self.initial = prefix
                for country_code in values:
                    country_name = locale.territories.get(country_code)
                    if country_name:
                        choices.append((prefix, "%s %s" % (country_name, prefix)))
        sorted_choices = sorted(choices, key=lambda item: item[1])
        if initial:
            if not isinstance(initial, tuple):
                raise Exception(
                    "Custom Error: The initial argument must be a 2-tuple. "
                    r"For example, ('+1', 'United States +1')"
                )
            sorted_choices[0] = initial

        Select.__init__(self=self, choices=sorted_choices)



class CustomPhoneNumberPrefixWidget(MultiWidget):
    """
    A Widget that splits phone number input into:
    - a country select box for phone prefix
    - an input for local phone number
    """

    def __init__(self, attrs=None, initial=None):
        widgets = (CustomPhonePrefixSelect(initial), TextInput())
        super(CustomPhoneNumberPrefixWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            if type(value) == PhoneNumber:
                if value.country_code and value.national_number:
                    return ["+%d" % value.country_code, value.national_number]
            else:
                return value.split(".")
        return [None, ""]

    def value_from_datadict(self, data, files, name):
        values = super(CustomPhoneNumberPrefixWidget, self).value_from_datadict(
            data, files, name
        )
        if all(values):
            return "%s.%s" % tuple(values)
        return ""
