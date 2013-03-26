
#!/usr/bin/env python

import os
os.environ['DJANGO_SETTINGS_MODULE']='wikipbx.settings'

from wikipbx.wikipbxweb.models import *


def main():
    accounts = Account.objects.all()
    for account in accounts:
        set_extension_priorities(account)

def set_extension_priorities(account):
    extensions = Extension.objects.filter(account=account)
    counter = 0
    for ext in extensions:
        print "setting %s ext %s priority to %s" % (account,
                                                    ext.id,
                                                    counter)
        ext.priority_position = counter
        ext.save()
        counter += 1


if __name__=="__main__":
    main()


