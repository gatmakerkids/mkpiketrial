import datetime
import pytz

from .models import *
from .forms import*

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django import template
from django.template import loader

import requests
import json

import os

PIKE_SITE = os.environ.get('PIKE_SITE_ENVAR')
PIKE_CLIENT_ID = os.environ.get('PIKE_CLIENT_ID_ENVAR')
PIKE_TOKEN = os.environ.get('PIKE_TOKEN_ENVAR')

# Create your views here.
def index(request):
    template = loader.get_template('trialreg/index.html')
    form = Register()
    context = {
        'form':form,
    }
    if not request.method == 'POST':
        return HttpResponse(template.render(context, request))

    form = Register(request.POST)
    context['form']=form
    if not form.is_valid():
        return HttpResponse(template.render(context, request))

    parent_first_name = form.cleaned_data['parent_first_name']
    parent_last_name = form.cleaned_data['parent_last_name']
    child_first_name = form.cleaned_data['child_first_name']
    child_last_name = form.cleaned_data['child_last_name']
    email = form.cleaned_data['email']
    phone_number = form.cleaned_data['phone_number']
    event_occurrence_id = form.cleaned_data['time_slot']

    #check db to see if email and child name have enrolled in a trial via this service in the last N-months
    email_registrations = Registration.objects.filter(email=email)
    for registration in email_registrations.all():
        if registration.child_first_name==child_first_name and registration.child_last_name==child_last_name:
            if registration.date_registered > (pytz.timezone('UTC').localize(datetime.datetime.now()) - datetime.timedelta(days=6*30)):
                context['error']="It seems like you've already booked a trial for " + child_first_name + ' ' + child_last_name + " fairly recently. Please contact us at info@makerkids.com to book a trial for them."
                return HttpResponse(template.render(context, request))

    #double check event_occurrence, is a trial, is in future, isn't too far away, and isn't full
    #pike creds
    headers = {'Authorization':'Bearer ' + PIKE_TOKEN}
    payload = {'client_id':PIKE_CLIENT_ID}

    #pike event call
    target = PIKE_SITE + 'api/v2/desk/event_occurrences/' + str(event_occurrence_id)
    r=requests.get(target, headers=headers, params=payload)
    json_data=json.loads(r.text)
    import pdb; pdb.set_trace()
    event_occurrence=json_data['event_occurrences'][0]

    #if not a trial return fail context error
    ###(this is really only possible if people maliciously edit the form's drowndown id values)
    if not (('Trial' or 'trial') in event_occurrence['name']):
        context['error']='That is not a trial.'
        return HttpResponse(template.render(context, request))


    #if start datetime < current datetime then return fail context error
    start = datetime.datetime.strptime(event_occurrence['start_at'].rstrip('Z'), '%Y-%m-%dT%H:%M:%S')
    if start < datetime.datetime.now():
        context['error']='It is too late to enroll in that trial.'
        return HttpResponse(template.render(context, request))


    #if start datetime < current datetime-45days then return fail context error
    if start < (datetime.datetime.now() - datetime.timedelta(days=45)):
        context['error']='That trial is too far away.'
        return HttpResponse(template.render(context, request))


    #if remainingg_cap<1 return fail context error
    if event_occurrence['capacity_remaining'] < 1:
        context['error']='That trial is full.'
        return HttpResponse(template.render(context, request))

    #check if parent exists in pike (by email)
    target = PIKE_SITE + 'api/v2/desk/people/search?q=' + str(email)
    payload = {'fields':'email'}
    r=requests.get(target, headers=headers, params=payload)
    json_data=json.loads(r.text)
    if json_data['results']:
        manager_id = json_data['results'][0]['id']
    #if not create parent and get id
    else:
        target = PIKE_SITE + 'api/v2/desk/people'
        payload = {
            'first_name':parent_first_name,
            'last_name':parent_last_name,
            'email':email,
            'phone_number':phone_number,
        }
        r=requests.post(target, headers=headers, params=payload)
        json_data=json.loads(r.text)
        manager_id = json_data['people'][0]['id']

    #check if kid exists in pike as dependent of parent
    target = PIKE_SITE + 'api/v2/desk/people/' + str(manager_id)
    payload = {
        'include_relationships':True,
    }
    r.request.get(target, headers=headers, params=payload)
    json_data=json.loads(r.text)
    dependent_ids = [] #track existing depends for later put call to update manager's dependents
    dependent_id = ''
    if len(json_data['people'][0]['dependents']) > 0:
        for dependent in json_data['people'][0]['dependents']:
            dependent_ids.append(dependent['id'])
            if dependent['first_name'] == child_first_name and dependent['last_name'] == child_last_name:
                dependent_id = dependent['id']
    #create and them associate dependent if they don't exist
    if dependent_id == '':
        target = PIKE_STIE + 'api/v2/desk/people'
        payload = {
            'first_name':child_first_name,
            'last_name':child_last_name,
            'guardian_name':parent_first_name + ' ' + parent_last_name,
            'guardian_email':email,
        }
        r.requests.post(target, headers=headers, params=payload)
        json_data=json.loads(r.text)
        dependent_id = json_data['people'][0]['id']
        dependent_ids.append(dependent_id)

        target = PIKE_SITE + 'api/v2/desk/people' + str(manager_id)
        payload = {
            'dependents':dependent_ids,
        }
        r.requests.put(target, headers=headers, params=payload)

    #enroll dependent in event_occurence
    target = PIKE_SITE + 'api/v2/desk/visits'
    payload = {
        'visit':{
            'person_id':dependent_id,
            'event_occurence_id':event_occurence_id,
            'restrictions':['full'],
        }
    }
    r.requests.post(target, headers=headers, params=payload)

    #document in db
    new_registration = Registration(
        parent_first_name=parent_first_name,
        parent_last_name=parent_last_name,
        child_first_name=child_first_name,
        child_last_name=child_last_name,
        phone_number=phone_number,
        email=email,
        event_occurrence_id=event_occurrence_id,
        date_registered=datetime.datetime.now(),
    )
    new_registration.save()

    return HttpResponseRedirect('success/' + str(event_occurrence_id))


def success(request, event_occurrence_id):
    template = loader.get_template('trialreg/success.html')

    #get the event_occurrence
    target = PIKE_SITE + 'api/v2/desk/event_occurrences/' + str(event_occurrence_id)
    headers = {'Authorization':'Bearer ' + PIKE_TOKEN}
    payload = {'client_id':PIKE_CLIENT_ID}
    r=requests.get(target, headers=headers, params=payload)
    json_data=json.loads(r.text)
    event_occurrence=json_data['event_occurrences'][0]
    start = datetime.datetime.strptime(event_occurrence['start_at'].rstrip('Z'), '%Y-%m-%dT%H:%M:%S')
    local_tz = pytz.timezone('America/Toronto') # use your local timezone name here
    local_start = start.replace(tzinfo=pytz.utc).astimezone(local_tz)
    context = {
        'date' : local_start.strftime("%A %b. %d"),
        'event' : event_occurrence['name'].split('- ')[0].strip(),
        'time' :  local_start.strftime("%I:%M%p") + " EST",
    }
    return HttpResponse(template.render(context, request))


def handler400(request, exception=None):
    context = {}
    response = render(context, 'trialreg/400.html')
    response.status_code = 400
    return response
def handler403(request, exception=None):
    context = {}
    response = render(context, 'trialreg/403.html')
    response.status_code = 403
    return response
def handler404(request, exception=None):
    context = {}
    response = render(context, 'trialreg/404.html')
    response.status_code = 404
    return response
def handler500(request, exception=None):
    context = {}
    response = render(context, 'trailreg/500.html')
    response.status_code = 500
    return response
