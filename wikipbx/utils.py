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
Stas Shtin <antisvin@gmail.com>
"""

import re
import datetime, urllib2
from random import choice
import string


def xml_snippet_no_header(serialized_xml):
    """
    generate an xml snippet suitable for inserting
    (strip off hte <?xml header stuff)

    Test cases:
    content = '<?xml version="1.0" ?><yo>sucks</yo>'
    content = '<?xml version="1.0" ?>\n<yo>sucks</yo>'
    """
    # match anchored at beginning of line, followed by <?xml,
    # followed by any number of any character EXCEPT >, followed
    # by >
    regex = '^(\s*)<\?xml([^>]*)>'
    matchstr = re.compile(regex, re.MULTILINE)
    result = matchstr.search(serialized_xml)
    if (result != None):
        serialized_xml = matchstr.sub("",serialized_xml)
    return serialized_xml
 
class DownloadError(Exception):
    """
    This exception is raised if file download fails.
    """

def download_url(url, path=None):
    """
    Fetch the content from a url, write to file or a string.

    @param url: URL to fetch.
    @type url: str.
    @param path: file path to write, None means writing to a string buffer.
    @type path: str.
    @return: string buffer with result or None.
    @raises: DownloadError.
    """
    if path:
        dst = file(path, 'w')
    else:
        dst = StringIO()

    try:
        req = urllib2.Request(url)
        result = urllib2.urlopen(req)
        stringbuffer = []
        while 1:
            data = result.read(1024)
            stringbuffer.append(data)
            if not len(data):
                break
            dst.write(data)
        if path:
            dst.close()
            return None
        else:
            return dst.getvalue()
    except:
        raise DownloadError()

def generate_passwd(length=8, chars=string.letters + string.digits):
    """
    Generate random passwords
    """
    return ''.join(choice(chars) for i in xrange(length))
