from django.conf import settings
from django.core import urlresolvers
from django.template import Library

register = Library()

@register.filter
def pretty(value):
    bits = value.title().replace('Ivr', 'IVR').split('_')
    for i in xrange(len(bits) - 1, 0, -1):
        if bits[i - 1] == 'Mod':
            bits[i -1] = '_'.join((bits[i - 1], bits[i])).capitalize()
            del bits[i]
    return ' '.join(bits)


@register.simple_tag
def admin_link():
    if getattr(settings, 'ENABLE_DB_ADMIN', False):
        return (
            '<div class="menu-entry">'
            '<img src="/site_media/icons/database.png"><a href="%s">DB Admin'
            '</a></div>' % urlresolvers.reverse('admin:index'))
    else:
        return ''
