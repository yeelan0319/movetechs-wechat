from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^create', views.create),
    url(r'^read/([0-9]+)/*$', views.update_state_read),
    url(r'^star/([0-9]+)/*$', views.update_state_star),
    url(r'^unstar/([0-9]+)/*$', views.update_state_unstar),
    url(r'^week/([0-9]+)/*$', views.view_by_week),
    url(r'^name/(\w+)/*$', views.view_by_name),
    url(r'^list-star/*$', views.view_by_star),
    url('', views.view, name='index'),
]