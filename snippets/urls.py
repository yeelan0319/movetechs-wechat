from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^create', views.create),
    url(r'^read/([0-9]+)/$', views.update_state_read),
    url(r'^done/([0-9]+)/$', views.update_state_done),
    url(r'^week/([0-9]+)/$', views.view_by_week),
    url('', views.view, name='index'),
]