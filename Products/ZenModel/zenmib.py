##############################################################################
#
# Copyright (C) Zenoss, Inc. 2007, 2009, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

"""zenmib
   The zenmib program converts MIBs into python data structures and then
(by default) adds the data to the Zenoss DMD.  Essentially, zenmib is a
wrapper program around the smidump program, whose output (python code) is
then executed "inside" the Zope database.

 Overview of terms:
   SNMP Simple Network Management Protocol
      A network protocol originally based on UDP which allows a management
      application (ie SNMP manager) to contact and get information from a
      device (ie router, computer, network-capable toaster).  The software
      on the device that is capable of understanding SNMP and responding
      appropriately is called an SNMP agent.

   MIB Management of Information Base
      A description of what a particular SNMP agent provides and what
      traps it sends.  A MIB is a part of a tree structure based on a root
      MIB.  Since a MIB is a rooted tree, it allows for delegation of areas
      under the tree to different organizations.

   ASN Abstract Syntax Notation
      The notation used to construct a MIB.

   OID Object IDentifier
      A MIB is constructed of unique identifiers


 Background information:
   http://en.wikipedia.org/wiki/Simple_Network_Management_Protocol
       Overview of SNMP.

   http://www.ibr.cs.tu-bs.de/projects/libsmi/index.html?lang=en
       The libsmi project is the creator of smidump.  There are several
       interesting sub-projects available.

   http://net-snmp.sourceforge.net/
       Homepage for Net-SNMP which is used by Zenoss for SNMP management.

   http://www.et.put.poznan.pl/snmp/asn1/asn1.html
       An overview of Abstract Syntax Notation (ASN), the language in
       which MIBs are written.
"""

import os
import os.path
import re
import sys
import tempfile

import Globals

from Products.ZenUtils.ZCmdBase import ZCmdBase
from Products.ZenUtils.mib.pkgmgr import PackageManager
from Products.ZenUtils.mib.config import SMIConfigFile
from Products.ZenUtils.mib.tools import (
    SMIDumpTool, evaluate_dump, group_dump_by_filename
)
from Products.ZenUtils.Utils import zenPath, unused

unused(Globals)

CHUNK_SIZE = 50

# Used to convert dictionary values in smidump output to raw strings
# "key": "value" becomes "key": r"value"
# This helps exec handle backslashes.
_DICT_STRING_VALUE_PATTERN = re.compile(r'(:\s*)"')


def _unique(iterable):
    """Generator producing unique items from the iterable while
    preserving the original order of those items.
    """
    seen = set()
    for item in iterable:
        if item not in seen:
            seen.add(item)
            yield item


class ZenMib(ZCmdBase):
    """
    """

    def _logException(self, mesg, *args):
        if self.log.isDebugEnabled():
            self.log.exception(mesg, *args)
        else:
            self.log.error(mesg, *args)

    def _saveDump(self, dump):
        path = self.options.pythoncodedir
        if not os.path.exists(path):
            self.log.warning("Python code dir not found: %s", path)
            return
        if not os.path.isdir(path):
            self.log.warning("Python code dir is not a directory: %s", path)
            return
        for filename, content in group_dump_by_filename(dump):
            pyfile = os.path.join(path, filename + ".py")
            with open(pyfile, 'w') as fd:
                fd.write(content)
                fd.flush()

    def _evalDump(self, dump):
        # evaluate_dump returns a generator.
        try:
            mibdef_generator = evaluate_dump(dump)
            while True:
                try:
                    yield next(mibdef_generator)
                except StandardError as ex:
                    self._logException(
                        "Failed to evaluate a MIB definition: %s", ex
                    )
        except StandardError as ex:
            self._logException(
                "Failed to evaluate MIB definition dump: %s", ex
            )
            raise StopIteration()

    def _processSavedDump(self, filename):
        try:
            dump = open(filename).read()
        except IOError as ex:
            self._logException("Failed to read %s: %s", filename, ex)
        else:
            for mibdef in self._evalDump(dump):
                try:
                    self._loadMIB(mibdef)
                except Exception as ex:
                    self._logException(
                        "Failed to load a MIB definition "
                        "from file %s: %s", filename, ex
                    )

    def _getMIBFiles(self):
        """Returns a list of files containing the MIBs to load into the DMD.

        @returns {list} List of MIBFile objects.
        """
        sources = self.args if self.args else [self.options.mibsdir]

        mibfiles = set()
        for source in sources:
            try:
                pkg = self._pkgmgr.get(source)
                mibfiles.update(pkg.extract())
            except Exception as ex:
                self._logException("Invalid argument %s: %s", source, ex)

        if mibfiles:
            self.log.debug(
                "Found MIB files to load: %s", ', '.join(f for f in mibfiles)
            )

        return list(_unique(mibfiles))

    def main(self):
        """
        Main loop of the program
        """
        if self.options.evalSavedPython:
            for filename in _unique(self.options.evalSavedPython):
                self._processSavedDump(filename)
            return

        self.pkgmgr = PackageManager(
            self.log, self.options.downloaddir, self.options.extractdir
        )

        try:
            mibfiles = self._getMIBFiles()
            paths = [zenPath("share", "mibs"), self.options.mibdepsdir]
            with SMIConfigFile(path=paths) as cfg:
                tool = SMIDumpTool(config=cfg)
                # returns string containing all the MIB definitions found
                # in the provided set of MIBFile objects.
                dump = tool.run(*mibfiles)

                if self.options.keeppythoncode:
                    self._saveDump(dump)

                moduleMgr = MIBModuleManager.make(self.dmd)
                for mibdef in self._evalDump(dump):
                    try:
                        self._loadMIB(mibdef, moduleMgr)
                    except Exception as ex:
                        self._logException(
                            "Failed to load a MIB definition: %s", ex
                        )
        except Exception as ex:
            self._logException(
                "Unable to create smidump's config file: %s", ex
            )

    def _loadMIB(self, mibdef):
        """
        """
        # Standard MIB attributes that we expect in all MIBs
        MIB_MOD_ATTS = ('language', 'contact', 'description')

        self.syncdb()

        mibName = mibdef['moduleName']

        # Check to see if any MIB definitions in fileName have already
        # been loaded into Zenoss. If so, warn but don't fail
        dmdMibPath = self.options.path
        mibModule = next(
            iter(self.dmd.Mibs.mibs.findObjectsById(mibName)), None
        )
        if not mibModule:
            # Create the container for the MIBs and define meta-data.
            # In the DMD this creates another container class which
            # contains mibnodes.  These data types are found in
            # Products.ZenModel.MibModule and Products.ZenModel.MibNode
            mibModule = self.dmd.Mibs.createMibModule(mibName, dmdMibPath)
        else:
        if dmdMibDict is not None and mibName in dmdMibDict:
            dmdMibPath = dmdMibDict[mibName]
            self.log.warn(
                "MIB definition %s is already loaded at %s. "
                "Will update it.", mibName, dmdMibPath
            )
            mibModule = self.dmd.Mibs.mibs.findObjectsById(mibName)[0]
        else:
            # Create the container for the MIBs and define meta-data.
            # In the DMD this creates another container class which
            # contains mibnodes.  These data types are found in
            # Products.ZenModel.MibModule and Products.ZenModel.MibNode
            mibModule = self.dmd.Mibs.createMibModule(mibName, dmdMibPath)

        def gen():
            for key, val in mibdef[mibName].iteritems():
                if key in MIB_MOD_ATTS:
                    yield key, val

        for key, val in gen():
            setattr(mibModule, key, val)
        self.commit("Loaded MIB %s into the DMD" % mibName)

        nodesAdded = self.addMibEntries('nodes', pythonMib, mibModule)
        trapsAdded = self.addMibEntries(
            'notifications', pythonMib, mibModule
        )
        self.log.info(
            "Parsed %d nodes and %d notifications from %s",
            nodesAdded, trapsAdded, mibName
        )

        # Add the MIB tree permanently to the DMD unless --nocommit flag.
        msg = "Loaded MIB %s into the DMD" % mibName
        self.commit(msg)
        if not self.options.nocommit:
            self.log.info(msg)

    def parseOptions(self):
        """
        """
        super(ZenMib, self).parseOptions()

        # Verify MIB dependency search directory is valid. Fail if not.
        if not os.path.exists(self.options.mibdepsdir):
            self.log.error(
                "'mibdepsdir' path not found: %s", self.options.mibdepsdir
            )
            sys.exit(1)

    def buildOptions(self):
        """
        Command-line options
        """
        super(ZenMib, self).buildOptions()
        self.parser.add_option(
            '--mibsdir', dest='mibsdir', default=zenPath('share/mibs/site'),
            help="Directory of input MIB files [default: %default]"
        )
        self.parser.add_option(
            '--mibdepsdir', dest='mibdepsdir', default=zenPath('share/mibs'),
            help="Directory of input MIB files [default: %default]"
        )
        self.parser.add_option(
            '--path', dest='path', default="/",
            help="Path to load MIB into the DMD [default: %default]"
        )
        self.parser.add_option(
            '--nocommit', dest='nocommit', action='store_true', default=False,
            help="Don't commit the MIB to the DMD after loading"
        )
        self.parser.add_option(
            '--keeppythoncode', dest='keeppythoncode',
            action='store_true', default=False,
            help="Don't commit the MIB to the DMD after loading"
        )
        self.parser.add_option(
            '--pythoncodedir', dest='pythoncodedir',
            default=tempfile.gettempdir() + "/mib_pythoncode/",
            help="This is the directory where the converted MIB will be "
            "output [default: %default]"
        )
        self.parser.add_option(
            '--downloaddir', dest='downloaddir',
            default=tempfile.gettempdir() + "/mib_downloads/",
            help="This is the directory where the MIB will be downloaded "
            "[default: %default]"
        )
        self.parser.add_option(
            '--extractdir', dest='extractdir',
            default=tempfile.gettempdir() + "/mib_extract/",
            help="This is the directory where unzipped MIB files will be "
            "stored [default: %default]"
        )
        self.parser.add_option(
            '--evalSavedPython', dest='evalSavedPython',
            action='append', default=[],
            help="Execute the Python code previously generated and saved"
        )
        self.parser.add_option(
            '--removemiddlezeros', dest='removemiddlezeros',
            action='store_true', default=False,
            help="Remove zeros found in the middle of the OID"
        )


if __name__ == '__main__':
    zm = ZenMib()
    zm.main()
