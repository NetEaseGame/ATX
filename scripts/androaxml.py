#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2012, Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
#
# Androguard is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Androguard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Androguard.  If not, see <http://www.gnu.org/licenses/>.

import os
__dir__ = os.path.relpath(os.path.dirname(os.path.abspath(__file__))) 

import sys
sys.path.append(os.path.join(__dir__, "androguard.zip"))

from optparse import OptionParser
from xml.dom import minidom
import codecs
import string

from androguard.core import androconf
from androguard.core.bytecodes import apk


#option_0 = { 'name' : ('-i', '--input'), 'help' : 'filename input (APK or android\'s binary xml)', 'nargs' : 1 }
option_1 = {'name' : ('-f', '--format'), 
    'help': 'output format', 
    'nargs': 1,
    'default': '$package'
    }
option_2 = {
    'name': ('-v', '--version'), 
    'help':'version of the API', 
    'action': 'count' 
    }
options = [option_1, option_2]

def xml2parse(dom, strformat='$package/$activity'):
    root = dom.getElementsByTagName("manifest")[0]
    package = root.getAttribute('package')
    activity = ''
    for e in root.getElementsByTagName('activity'):
        name = e.getAttribute('android:name')
        t = e.getElementsByTagName('intent-filter')
        if t:
            activity = name
    print string.Template(strformat).safe_substitute(
            package=package, activity = activity)

def main(options, filename) :
    if filename != None :
        buff = ""

        ret_type = androconf.is_android(filename)
        if ret_type == "APK":
            a = apk.APK(filename)
            dom = a.get_android_manifest_xml()
            #buff = a.get_android_manifest_xml().toprettyxml(encoding="utf-8")
            #a.get_activities()
            xml2parse(dom)
        elif ".xml" in filename:
            ap = apk.AXMLPrinter(open(filename, "rb").read())
            buff = minidom.parseString(ap.get_buff()).toprettyxml(encoding="utf-8")
        else:
            print "Unknown file type"
            return

        #if options.output != None :
        #    fd = codecs.open(options.output, "w", "utf-8")
        #    fd.write( buff )
        #    fd.close()
        #else :
        #    print buff

    elif options.version != None :
        print "Androaxml version %s" % androconf.ANDROGUARD_VERSION

if __name__ == "__main__" :
    parser = OptionParser()
    for option in options :
        param = option['name']
        del option['name']
        parser.add_option(*param, **option)

    options, arguments = parser.parse_args()
    if len(arguments) == 0:
        sys.exit('use --help for more help')

    sys.argv[:] = arguments
    main(options, arguments[0])
