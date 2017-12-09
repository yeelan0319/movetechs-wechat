from django.conf.urls import url

from . import views

urlpatterns = [
    url('create', views.create, name='create'),
    url('week/<int:week_no>', views.week, name='week'),
    url('', views.index, name='index'),
]