import os
from zExceptions import BadRequest

BASE_PATH = "/zport/dmd/Mibs"

__all__ = ("MibOrganizerPath", "ModuleManager", "Module", "getMibModuleMap")


class MibOrganizerPath(object):
    """Encapsulates a MibModule's organizer path in DMD.
    """

    def __init__(self, path):
        """Initialize an instance of MibOrganizerPath.

        The path value can be a path relative to /zport/dmd/Mibs
        or a full path starting from /zport.

        @param {str} Path to module.
        """
        if path[0:len(BASE_PATH)] != BASE_PATH:
            path = os.path.join(BASE_PATH, path)
        self._path = path
        self._relpath = self._path[len(BASE_PATH)+1:]

    @property
    def path(self):
        """Returns the full path of the organizer.
        """
        return self._path

    @property
    def organizer(self):
        """Returns the relative path of the organizer.
        """
        return self._relpath


def getMibModuleMap(dmd):
    """Return a dict mapping module names to their organizer in DMD.

    @returns {dict str:MibOrganizerPath}
    """
    registry = {}
    for module in dmd.Mibs.getSubInstancesGen("mibs"):
        path = module.getPrimaryPath()
        organizerPath, moduleName = "/".join(path[:-1]), path[-1]
        registry[moduleName] = MibOrganizerPath(organizerPath)
    return registry


class Module(object):
    """Wraps a dict object containing a MIB definition.
    """

    _ATTRIBUTES = ('language', 'contact', 'description')

    def __init__(self, mib):
        self._mib = mib

    @property
    def name(self):
        return self._mib.get("moduleName", None)

    @property
    def attributes(self):
        return {
            key: self._mib.get(key)
            for key in self._ATTRIBUTES if key in self._mib
        }

    @property
    def nodes(self):
        return self._mib.get("nodes")

    @property
    def notifications(self):
        return self._mib.get("notifications")

    def getattr(self, attr):
        """Return the value of the given attribute.
        """
        return self._mib.get(attr, None)


class ModuleManager(object):
    """Manages the adding, updating, and deletion of MIB modules in DMD.
    """

    def __init__(self, dmd, registry):
        """Initialize an instance of ModuleManager.

        @param registry {dict} Initial module to organizer mapping.
        @param organizer {MibOrganizerPath} Add MibModules to this organizer.
        """
        self._dmd = dmd
        self._registry = registry
        self._organizers = set(self._registry.values())

    def add(self, module, organizer):
        """Add MIB module to DMD.
        """
        # 1. Add module to path if module doesn't already exist on some path.
        # 2. Add/update module attributes
        # 3. Add module nodes
        # 4. Add module notifications

        mibmod = self._getMibModule(module.name, organizer)

        for attr in module.attributes:
            setattr(mibmod, attr, module.getattr(attr))

        categories = {
            "nodes": (mibmod.createMibNode, module.nodes),
            "notifications":
                (mibmod.createMibNotification, module.notifications),
        }

        for function, data in categories.items():
            for name, values in data.itemiter():
                self._addItem(function, name, values, module.name)

    def _getMibModule(self, name, organizer):
        orig_organizer = self._registry.get(name)
        if orig_organizer:
            return self._dmd.unrestrictedTraverse(
                orig_organizer.path + "/" + name
            )
        return self._dmd.createMibModule(name, organizer.organizer)

    def _addItem(self, function, name, values, moduleName):
        try:
            function(name, logger=self.log, **values)
        except BadRequest:
            self.log.warn(
                "Unable to add %s id '%s' as this name is "
                "reserved for use by Zope", "node", name
            )
            newName = '_'.join([name, moduleName])
            self.log.warn(
                "Trying to add %s '%s' as '%s'",
                "node", name, newName
            )
            try:
                function(newName, logger=self.log, **values)
            except Exception:
                self.log.warn(
                    "Unable to add %s id '%s' -- skipping",
                    "node", newName
                )
            else:
                self.log.warn(
                    "Renamed '%s' to '%s' and added to MIB %s",
                    name, newName, "node"
                )
