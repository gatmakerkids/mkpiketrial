from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


# Create your models here.
class Registration(models.Model):
    parent_first_name = models.CharField(max_length=50)
    parent_last_name = models.CharField(max_length=50)
    child_first_name = models.CharField(max_length=50)
    child_last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone_number = PhoneNumberField()
    event_occurrence_id = models.CharField(max_length=50)
    date_registered = models.DateTimeField()
