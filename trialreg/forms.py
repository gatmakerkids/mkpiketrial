from django import forms
from django.core import validators
from django.core.validators import validate_email

from .models import *

from phonenumber_field.formfields import PhoneNumberField
from .widgets import CustomPhoneNumberPrefixWidget

from captcha.fields import CaptchaField

import datetime
import requests
import json
import pytz

class Register(forms.Form):
    parent_first_name = forms.CharField(max_length=50)
    parent_last_name = forms.CharField(max_length=50)
    child_first_name = forms.CharField(max_length=50)
    child_last_name = forms.CharField(max_length=50)
    email = forms.EmailField(validators=[validate_email])
    phone_number = PhoneNumberField(
        widget=CustomPhoneNumberPrefixWidget(
            initial=('+1', 'Canada +1'),
            attrs={'placeholder':'416-555-5555'},
        )
    )

    def get_trials():
        client_id = "FKIsXUGoiUINEvtjL15CL0HUvsxEhJk2I9rdf9li"
        token = "7S61Wa5ioNgBQ70fpqBkPMJeNWpxRW7Rt8FEOuZj"

        #get all events
        target = "https://makerkids.pike13.com/api/v2/desk/event_occurrences"
        headers = {'Authorization':'Bearer ' + token}
        payload = {'client_id':client_id, "from":datetime.datetime.now(), "to":datetime.datetime.now()+datetime.timedelta(days=4)} #days>45 breaks pike api
        r=requests.get(target, headers=headers, params=payload)
        json_data=json.loads(r.text)

        #find trials with capacity
        open_trials = []
        for event_occurrence in json_data['event_occurrences']:
            if('Trial' or 'trial') in event_occurrence['name'] and event_occurrence['capacity_remaining']>0:
                open_trials.append(event_occurrence)

        #sort by datetime
        open_trials.sort(key=lambda x: x['start_at'])

        #format list of tuple items
        trial_classes = ['hi']
        '''
        for event_occurrence in open_trials:
            start = datetime.datetime.strptime(event_occurrence['start_at'].rstrip('Z'), '%Y-%m-%dT%H:%M:%S')
            end = datetime.datetime.strptime(event_occurrence['end_at'].rstrip('Z'), '%Y-%m-%dT%H:%M:%S')
            local_tz = pytz.timezone('America/Toronto') # use your local timezone name here
            local_start = start.replace(tzinfo=pytz.utc).astimezone(local_tz)
            local_end = end.replace(tzinfo=pytz.utc).astimezone(local_tz)

            title = event_occurrence['name']
            title = title.split(' (Eastern Standard Time)')[0]
            title = title.split(' - Robotics, Coding, Minecraft')[0]
            title = title.split(' Mini Maker Trial')[0]
            try:
                title = title.split(' Virtual Trial:')[0] + title.split(' Virtual Trial:')[1]
            except:
                pass
            title = title.split(' Trial')[0]

            temp_tup = (event_occurrence['id'], local_start.strftime("%a %b. %d") + ", " + local_start.strftime("%I:%M%p") + "-" + local_end.strftime("%I:%M%p") + " EST/EDT | "  + title)
            trial_classes.append(temp_tup)
        '''

        #return the list of tuples
        return trial_classes
    time_slot = forms.ChoiceField(choices=get_trials, required=True)

    #captcha = CaptchaField()

    def clean(self):
        cleaned_data = super(Register, self).clean()
