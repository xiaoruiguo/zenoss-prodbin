#################################################################
#
#   Copyright (c) 2002 Zentinel Systems, Inc. All rights reserved.
#
#################################################################

__doc__="""HardDisk

HardDisk is a collection of devices and subsystems that make
up a business function

$Id: HardDisk.py,v 1.7 2004/04/06 22:33:24 edahl Exp $"""

__version__ = "$Revision: 1.7 $"[11:-2]

from Globals import DTMLFile
from Globals import InitializeClass

from Products.ZenRelations.RelSchema import *

from HWComponent import HWComponent

def manage_addHardDisk(context, id, title = None, REQUEST = None):
    """make a filesystem"""
    hd = HardDisk(id, title)
    context._setObject(id, hd)
    hd = context._getOb(id)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(context.absolute_url()
                                     +'/manage_main') 

addHardDisk = DTMLFile('dtml/addHardDisk',globals())


class HardDisk(HWComponent):
    """HardDisk object"""

    portal_type = meta_type = 'HardDisk'

    manage_editHardDiskForm = DTMLFile('dtml/manageEditHardDisk',globals())
    
    description = ""
    hostresindex = 0

    _properties = (
                 {'id':'description', 'type':'string', 'mode':'w'},
                 {'id':'hostresindex', 'type':'int', 'mode':'w'},
                )    

    _relations = HWComponent._relations + (
        ("device", ToOne(ToManyCont, "Device", "harddisks")),
        )

    
    factory_type_information = ( 
        { 
            'id'             : 'HardDisk',
            'meta_type'      : 'HardDisk',
            'description'    : """Arbitrary device grouping class""",
            'icon'           : 'HardDisk_icon.gif',
            'product'        : 'ZenModel',
            'factory'        : 'manage_addHardDisk',
            'immediate_view' : 'viewHardDisk',
            'actions'        :
            ( 
                { 'id'            : 'status'
                , 'name'          : 'Status'
                , 'action'        : 'viewHardDisk'
                , 'permissions'   : ('View',)
                },
                { 'id'            : 'viewHistory'
                , 'name'          : 'Changes'
                , 'action'        : 'viewHistory'
                , 'permissions'   : ('View',)
                },
            )
          },
        )

    def viewName(self): return self.description


InitializeClass(HardDisk)
