from django.urls import path

from . import views

app_name='trialreg'
urlpatterns = [
    path('', views.index, name='index'),
    path('success/<int:event_occurrence_id>/', views.success, name='success'),
]
