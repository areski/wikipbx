""" 
WikiPBX web GUI front-end for FreeSWITCH <www.freeswitch.org>
Copyright (C) 2007, Branch Cut <www.branchcut.com>

Version: MPL 1.1

The contents of this file are subject to the Mozilla Public License Version
1.1 (the "License"); you may not use this file except in compliance with
the License. You may obtain a copy of the License at
http://www.mozilla.org/MPL/

Software distributed under the License is distributed on an "AS IS" basis,
WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
for the specific language governing rights and limitations under the
License.

The Original Code is - WikiPBX web GUI front-end for FreeSWITCH

The Initial Developer of the Original Code is
Traun Leyden <tleyden@branchcut.com>
Portions created by the Initial Developer are Copyright (C)
the Initial Developer. All Rights Reserved.

Contributor(s):
Riccardo Magliocchetti (unbit sas) <riccardo.magliocchetti@gmail.com>
Stas Shtin <antisvin@gmail.com>
"""
from django import http
from django.template.loader import render_to_string
from django.core import serializers
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.views.generic import simple
from wikipbx.contacts import forms, statics
from wikipbx.contacts.models import Contact
from wikipbx.wikipbxweb import decorators


@decorators.require_admin
def contacts(request):
    account = request.user.get_profile().account
    contacts = Contact.objects.filter(account=account)
    export = forms.ExportContactForm()
    return simple.direct_to_template(
        request, 'contacts.html', {'contacts': contacts, 'export': export })

@decorators.require_admin
def edit_contact(request, contact_id):
    account = request.user.get_profile().account
    if contact_id is None:
        contact = Contact(account=account)
    else:
        contact = get_object_or_404(Contact, account=account, pk=contact_id)

    # Set is_explicit flag, but don't save model yet.
    contact.is_explicit = True

    if request.method == 'POST':
        form = forms.ContactForm(request.POST, instance=contact)

        if form.is_valid():
            contact = form.save()
            msg = _(u"Contact %s saved.") % contact
            return http.HttpResponseRedirect(
                reverse('contacts:list') + "?infomsg=%s" % msg)
    else:
        form = forms.ContactForm(instance=contact)

    return simple.direct_to_template(
        request, 'edit_contact.html', {'form': form})
    
@decorators.require_admin
def del_contact(request, contact_id):
    account = request.user.get_profile().account
    contact = get_object_or_404(Contact, account=account, pk=contact_id)
    contact.delete()
    msg = _(u"Contact %s deleted.") % contact
    return http.HttpResponseRedirect(
        reverse('contacts:list') + "?infomsg=%s" % msg)

@decorators.require_admin
def export_contacts(request):
    account = request.user.get_profile().account
    contacts = Contact.objects.filter(account=account)

    search_data = request.POST.get('search_data', None)

    if request.method == 'POST':
        export_type = request.POST.get('export_type', None)

        export = request.POST.get('export', None)

        if export and export_type in statics.EXPORT_FORMATS:
            # Filter only selected contacts.
            contacts = contacts.filter(
                pk__in=request.POST.getlist('contact-id'))

            # Render output file.
            file_name = '%s.%s' % (
                export_type, statics.get_extension(export_type))
            template_name = 'export/%s' % file_name
            result = render_to_string(template_name, {'contacts': contacts})
            response = http.HttpResponse(
                result, mimetype=statics.get_mimetype(export_type))

            # Set file name and return.
            response['Content-Disposition'] = 'filename=%s' % file_name
            return response

        elif search_data:
            # Search button clicked.
            contacts = contacts.filter(
                Q(first_name__icontains=search_data) |
                Q(last_name__icontains=search_data) |
                Q(work__icontains=search_data) |
                Q(home__icontains=search_data) |
                Q(mobile__icontains=search_data))

    export_form = forms.ExportContactForm()
    return simple.direct_to_template(
        request, 'contacts_export.html',
        {'contacts': contacts, 'export_form': export_form,
         'search_data': search_data})

@decorators.fs_address_only
def export_contacts_json(request, account_id):
    try:
        contacts = Contact.objects.filter(account__pk=account_id, is_explicit=True)
        json_serializer = serializers.get_serializer("json")()
        json = json_serializer.serialize(contacts, ensure_ascii=False)
    except:
        json = ""

    return http.HttpResponse(json)
