#################################################################
#
#   Copyright (c) 2002 Zentinel Systems, Inc. All rights reserved.
#
#################################################################

__doc__="""ManagedEntity

$Id: DeviceComponent.py,v 1.1 2004/04/06 21:05:03 edahl Exp $"""

from ZenModelRM import ZenModelRM
from EventView import EventView
from CricketView import CricketView

from Products.ZenRelations.RelSchema import *

class ManagedEntity(ZenModelRM, EventView, CricketView):
    """
    ManagedEntity is an entity in the system that is managed by it.
    Its basic property is that it can be classified by the ITClass Tree.
    Also has EventView and CricketView available.
    """

    # dict of cricket targets -> targettypes
    _cricketTargetMap = {}

    # list of cricket multigaphs (see CricketView.py)
    _mgraphs = []

    # primary snmpindex for this managed entity
    snmpindex = 0

    _properties = (
                 {'id':'snmpindex', 'type':'int', 'mode':'w'},
                )    

    _relations = (
        ("dependenices", ToMany(ToMany, "ManagedEntity", "dependants")),
        ("dependants", ToMany(ToMany, "ManagedEntity", "dependenices")),
    )
