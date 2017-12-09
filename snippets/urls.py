from django.conf.urls import url

from . import views

urlpatterns = [
    url('', views.index, name='index'),
    url('week/<int:week_no>', views.week, name='week'),
    url('create', views.create, name='create')
]