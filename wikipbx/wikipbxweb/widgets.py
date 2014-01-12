""" 
WikiPBX web GUI front-end for FreeSWITCH <www.freeswitch.org>
Copyright (C) 2010, Branch Cut <www.branchcut.com>

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
Stas Shtin <antisvin@gmail.com>
Portions created by the Initial Developer are Copyright (C)
the Initial Developer. All Rights Reserved.

Contributor(s): 
"""
from django.conf import settings
from django.forms import widgets as django_widgets
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

__all__ = (
    'ExtensionTemplateWidget', 'AuthCallWidget', 'RepeatedPasswordWidget')


class ExtensionTemplateWidget(django_widgets.Select):
    template_choices_code = None
    
    def render(self, name, value, attrs=None, choices=()):
        result = super(ExtensionTemplateWidget, self).render(
            name, value, attrs=attrs, choices=choices)
        result += (
            '''
<script>
var data = %s;\n
function add_to_template() {
  var template_element = document.getElementById("id_template");
  var actions_xml_element = document.getElementById("id_actions_xml");
  var value = data[template_element.value];
  if (template_element.value.substring(0, 8) == "endpoint") {
    var endpoint = document.getElementById("id_endpoint");
    value = value.replace("@@endpoint@@", endpoint.options[endpoint.selectedIndex].text);
  }
  actions_xml_element.value += value + "\\n\\n";
}
function update_endpoint_state() {
  var template_element = document.getElementById("id_template");
  var endpoint = document.getElementById("id_endpoint");
  endpoint.disabled = (template_element.value.substring(0, 9) != "endpoint");
}
</script>
<img src="%sicons/add.png" border="0" onClick="add_to_template()">'''
            ) % (str(self.template_choices_code or {}), settings.MEDIA_URL)
        return result


class AuthCallRenderer(django_widgets.RadioFieldRenderer):
    def render(self):
        """Outputs a <span> for this set of radio fields."""
        return mark_safe(u'\n'.join(
            '<span><img src="%sicons/%s.png"/>%s</span>' % (
                settings.STATIC_URL,
                ('lock' if w.choice_value == 'True' else 'lock_open'),
                force_unicode(w))
            for w in self))


class AuthCallWidget(django_widgets.RadioSelect):
    renderer = AuthCallRenderer


class RepeatedPasswordWidget(django_widgets.MultiWidget):
    """
    A widget with two password entries.
    """
    def __init__(self, widgets=None, attrs=None):
        if widgets is None:
            widgets = [
                django_widgets.PasswordInput,
                django_widgets.PasswordInput]
        super(RepeatedPasswordWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        return [value, value]

    def format_output(self, rendered_widgets):
        """
        Output widgets separated by BR tag.
        """
        return u'<br/>'.join(rendered_widgets)
