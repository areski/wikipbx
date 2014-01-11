from django.conf.urls import *

urlpatterns = patterns(
    'wikipbx.contacts.views',
    url(r'^$', 'contacts', name='list'),
    url(r'^add/$', 'edit_contact', { 'contact_id': None }, name='add'),
    url(r'^(?P<contact_id>\d+)/$', 'edit_contact', name='edit'),
    url(r'^(?P<contact_id>\d+)/delete/$', 'del_contact', name='delete'),
    url(r'^export/$', 'export_contacts', name='export'),
    url(r'^export/(?P<account_id>\d+)/json/$', 'export_contacts_json',
        name='export-json'),
)
