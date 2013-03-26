from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _


EXPORT_FORMATS = SortedDict((
    ('vcard_2_1', _('vCard 2.1')),
    ('vcard_3_0', _('vCard 3.0')),
    ('csv', _('CSV (Comma-separated values)')),
    ('csv_header', _('CSV with headers'))
))

get_extension = lambda format: 'vcf' if format.startswith('vcard') else 'csv'

get_mimetype = lambda format: (
    'text/x-vcard' if format.startswith('vcard') else 'text/csv')
