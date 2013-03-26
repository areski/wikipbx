from django.test import TestCase
from wikipbx.contacts.views import gigaset_export

VCF = \
u"""BEGIN:VCARD\r
VERSION:2.1\r
FN: Alice\r
N: Alice\r
TEL;HOME:123456789\r
END:VCARD\r

BEGIN:VCARD\r
VERSION:2.1\r
FN: Bob\r
N: Bob\r
TEL;HOME:123456789\r
END:VCARD\r

"""

class Account:
    def __init__(self, name, number):
        self.name = name
        self.number = number

class ContactTestCase(TestCase):
    def setUp(self):
        self.alice = Account('Alice', '123456789')
        self.bob = Account('Bob', '123456789')

    def test_gigaset_export(self):
        contacts = [self.alice, self.bob]
        vcf = gigaset_export(contacts).content
        self.assertEqual(vcf, VCF)

