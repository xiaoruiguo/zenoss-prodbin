###########################################################################
#
# This program is part of Zenoss Core, an open source monitoring platform.
# Copyright (C) 2007, 2011, Zenoss Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 or (at your
# option) any later version as published by the Free Software Foundation.
#
# For complete information please visit: http://www.zenoss.com/oss/
#
###########################################################################

from CollectionStatistic import CollectionStatistic
from PingTask import PingTask
from PingCollectionPreferences import PingCollectionPreferences
import nmap
import ping
import collections as _collections
 
# define a namedtuple to store hop results
TraceHop = _collections.namedtuple('TraceHop', 'ip rtt')
 
