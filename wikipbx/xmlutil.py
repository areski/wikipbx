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
"""

def firstElementTextByTagName(dom, tagname):
    elements = dom.getElementsByTagName(tagname)
    if not elements:
        return None

    element = elements[0]    
    return getText(element)    

def getText(elt):

    """ given an element, get its text.  if there is more than
    one text node child, just append all the text together.
    """
    result = ""
    children = elt.childNodes
    for child in children:
        if child.nodeType == child.TEXT_NODE:
            result += child.nodeValue
    return result

def getAttrValue(root_elt, elt_name, attr_name, attrname2match, attr2return):
    """
    Given
    <header name="Event-Subclass" value="sofia::register"></header>
    and the right params, return "sofia::register"
    """
    elements = root_elt.getElementsByTagName(elt_name)
    for element in elements:
        if not element.hasAttribute(attr_name):
            continue
        attr_name_val = element.getAttribute(attr_name)
        if not attr_name_val == attrname2match:
            # eg, does name="Event-Subclass" ?
            continue
        attrval2return = element.getAttribute(attr2return)
        return attrval2return
    return None
    
    
