from django.conf.urls import *


urlpatterns = patterns(
    'wikipbx.wikipbxweb.views',

    # General
    url(r'^$', 'index', name='index'),
    url(r'^dashboard/$', 'dashboard', name='dashboard'),
    url(r'^xml_dialplan/$', 'xml_dialplan', name='xml-dialplan'),
    url(r'^member/login/', 'memberlogin', name='member-login'),
    url(r'^member/logout/$', 'memberlogout', name='member-logout'),

    # Extensions
    url(r'^extensions/(?P<extension_id>\d+)/priority/(?P<action>\S+)/$',
        'ext_priority', name='extension-priority'),
    url(r'^extensions/$', 'extensions', name='extension-list'),
    url(r'^extensions/add/$', 'edit_extension', { 'extension_id': None },
        name='extension-add'),
    url(r'^extensions/(?P<extension_id>\d+)/$', 'edit_extension',
        name='extension-edit'),
    url(r'^extensions/(?P<extension_id>\d+)/delete/$', 'del_extension',
        name='extension-delete'),

    # Extension/IVR Actions    
    url(r'^extensions/(?P<extension_id>\d+)/actions/add/$', 'add_ext_action', 
        name='extension-action-add'),
    url(r'^extensions/ivrs/(?P<ivr_id>\d+)/actions/add/$', 'add_ivr_action', 
        name='ivr-action-add'),
    url(r'^extensions/actions/(?P<action_id>\d+)/delete/$', 'del_ext_action', 
        name='extension-action-delete'),
    url(r'^extensions/ivrs/actions/(?P<action_id>\d+)/delete/$',
        'del_ivr_action', name='ivr-action-delete'),

    # IVRs
    url(r'^ivrs/$', 'ivrs', name='ivr-list'),
    url(r'^ivrs/add/$', 'add_ivr', name='ivr-add'),
    url(r'^ivrs/(?P<ivr_id>\d+)/$', 'edit_ivr', name='ivr-edit'),
    url(r'^ivrs/(?P<ivr_id>\d+)/delete/$', 'del_ivr', name='ivr-delete'),
    url(r'^ivrs/xml/add/$', 'edit_ivr_xml', { 'ivr_id': None }, 'ivr-xml-add'),
    url(r'^ivrs/xml/(?P<ivr_id>\d+)/$', 'edit_ivr_xml', name='ivr-xml-edit'),

    # Accounts/users
    url(r'^accounts/$', 'accounts', name='account-list'),
    url(r'^accounts/add/$', 'add_account', name='account-add'),
    url(r'^accounts/(?P<account_id>\d+)/$', 'edit_account',
        name='account-edit'),
    url(r'^accounts/(?P<account_id>\d+)/delete/$', 'del_account',
        name='account-delete'),
    url(r'^users/(?P<account_id>\d+)/$', 'users', name='user-account'),
    url(r'^users/(?P<account_id>\d+)/add/$', 'add_user', name='user-add'),
    url(r'^users/(?P<account_id>\d+)/(?P<user_id>\d+)/$', 'edit_user',
        name='user-edit'),
    url(r'^users/(?P<account_id>\d+)/(?P<user_id>\d+)/delete/$', 'del_user',
        name='user-delete'),

    # SIP Profiles
    url(r'^profiles/$', 'sip_profiles', name='profile-list'),
    url(r'^profiles/add/$', 'add_sip_profile', name='profile-add'),
    url(r'^profiles/(?P<profile_id>\d+)/$', 'edit_sip_profile',
        name='profile-edit'),
    url(r'^profiles/(?P<profile_id>\d+)/delete/$', 'del_sip_profile',
        name='profile-delete'),
    
    # Gateways
    url(r'^gateways/$', 'gateways', name='gateway-list'),
    url(r'^gateways/add/$', 'add_gateway', name='gateway-add'),
    url(r'^gateways/(?P<gateway_id>\d+)/$', 'edit_gateway',
        name='gateway-edit'),
    url(r'^gateways/(?P<gateway_id>\d+)/delete/$', 'del_gateway',
        name='gateway-delete'),

    # Endpoints
    url(r'^endpoints/$', 'endpoints', name='endpoint-list'),
    url(r'^endpoints/add/$', 'add_endpoint', name='endpoint-add'),
    url(r'^endpoints/(?P<endpoint_id>\d+)/$', 'edit_endpoint',
        name='endpoint-edit'),
    url(r'^endpoints/(?P<endpoint_id>\d+)/delete/$', 'del_endpoint',
        name='endpoint-delete'), 
    url(r'^endpoints/(?P<endpoint_id>\d+)/extensions/$', 'exts4endpoint',
        name='endpoint-extension-list'),
    url(r'^eventsocket/$', 'event_socket', name='event-socket'),
    url(r'^endpoints/(?P<endpoint_id>\d+)/outgoing/$', 'outgoing2endpoint',
        name='outgoing-to-endpoint'),
    url(r'^click2call/$', 'click2call', name='click-to-call'),    

    # Soundclips
    url(r'^soundclips/$', 'soundclips', name='soundclip-list'),
    url(r'^soundclips/add/$', 'add_soundclip', name='soundclip-add'),
    # TODO: soundclip editing?
    url(r'^soundclips/(?P<soundclip_id>\d+)/delete/$', 'del_soundclip',
        name='soundclip-delete'),

    # CDRs
    url(r'^calls/records/add/$', 'add_cdr', name='cdr-add'),
    url(r'^calls/unmatched/$', UnmatchedCompletedCalls.as_view(),
        name='calls-unmatched'),
    url(r'^calls/matched/$', 'completedcalls', name='calls-matched'),

    # Server settings/logs
    url(r'^logs/$', 'server_logs', name='log-list'),
    url(r'^root/add/$', 'add_root', name='root-add'),

    # Freeswitch control
    url(r'^channels/$', ServerLogsView.as_view(), name='calls-live'),
    url(r'^channels/hangup/(?P<chan_uuid>\S+)/$', 'hangup_channels',
        name='channel-hangup'),
    url(r'^channels/hangup/$', 'hangup_channels', name='channel-hangup-all'),
    url(r'^channels/dialout/(?P<dest_ext_app>.+)/$', 'dialout',
        name='dialout'),
    url(r'^channels/broadcast/(?P<chan_uuid>\S+)/$', 'broadcast2channel',
        name='channel-broadcast'),
    url(r'^channels/transfer/(?P<chan_uuid>\S+)/$', 'transfer',
        name='channel-transfer'),

    # Mailserver
    url(r'^mailserver/config/$', 'config_mailserver', name='email-config'),
    url(r'^mailserver/test/$', 'test_mailserver', name='email-test'),
)
