##############################################################################
#
# Copyright (C) Zenoss, Inc. 2007, 2009, 2018 all rights reserved.
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
import sys
import tempfile

import Globals

from Products.ZenUtils.ZCmdBase import ZCmdBase
from Products.ZenUtils.mib import (
    PackageManager, SMIConfigFile, SMIDumpTool, ModuleManager,
    MibOrganizerPath, getMibModuleMap, MIBLoader
)
from Products.ZenUtils.Utils import zenPath, unused

unused(Globals)


def _unique(iterable):
    """Generator producing unique items from the iterable while
    preserving the original order of those items.
    """
    seen = set()
    for item in iterable:
        if item not in seen:
            seen.add(item)
            yield item


class BaseProcessor(object):
    """Base class.
    """

    def __init__(self, dmd, options):
        """
        """
        self._organizer = MibOrganizerPath(options.path)
        moduleRegistry = getMibModuleMap(dmd)
        self._moduleMgr = ModuleManager(dmd, moduleRegistry)


class MIBFileProcessor(object):
    """Load MIB files and add them to the DMD.
    """

    def __init__(self, dmd, options):
        """
        """
        super(MIBFileProcessor, self).__init__(dmd, options)
        self.pkgmgr = PackageManager(options.downloaddir, options.extractdir)
        self._savepath = \
            options.pythoncodedir if options.keeppythoncode else None
        self._mibdepsdir = options.mibdepsdir

    def run(self):
        mibfiles = self._getMIBFiles()
        paths = [zenPath("share", "mibs"), self._mibdepsdir]

        loaderArgs = (self._moduleMgr, self._organizer)

        with SMIConfigFile(path=paths) as cfg, \
                MIBLoader(*loaderArgs, savepath=self._savepath) as loader:
            tool = SMIDumpTool(config=cfg)
            # returns string containing all the MIB definitions found
            # in the provided set of MIBFile objects.
            dump = tool.run(*mibfiles)
            if dump:
                loader.load(dump)

    def _getMIBFiles(self):
        """Returns a list of files containing the MIBs to load into the DMD.

        @returns {list} List of MIBFile objects.
        """
        sources = self.args if self.args else [self.options.mibsdir]

        mibfiles = []
        for source in sources:
            try:
                pkg = self._pkgmgr.get(source)
                mibfiles.extend(pkg.extract())
            except Exception as ex:
                self._logException("Invalid argument %s: %s", source, ex)

        mibfiles = list(_unique(mibfiles))

        if mibfiles:
            self.log.debug(
                "Found MIB files to load: %s", ', '.join(f for f in mibfiles)
            )

        return mibfiles


class DumpFileProcessor(object):
    """Load previously saved MIB dump files and add them to the DMD.
    """

    def __init__(self, dmd, options, dumpfiles):
        """
        """
        super(MIBFileProcessor, self).__init__(dmd, options)
        self._dumpfiles = dumpfiles

    def run(self):
        """
        """
        with MIBLoader(self._moduleMgr, self._organizer) as loader:
            for filename in _unique(self._dumpfiles):
                try:
                    dump = open(filename).read()
                except IOError as ex:
                    self._logException("Failed to read %s: %s", filename, ex)
                else:
                    if dump:
                        loader.load(dump)


class ZenMib(ZCmdBase):
    """
    """

    def _logException(self, mesg, *args):
        if self.log.isDebugEnabled():
            self.log.exception(mesg, *args)
        else:
            self.log.error(mesg, *args)

    def run(self):
        """
        """
        self.verifyOptions()
        try:
            if self.options.evalSavedPython:
                processor = DumpFileProcessor(
                    self.dmd, self.options, self.options.evalSavedPython
                )
            else:
                processor = MIBFileProcessor(self.dmd, self.options)

            processor.run()
        except Exception as ex:
            self._logException("Failure: %s", ex)

    def verifyOptions(self):
        """
        """
        # Verify MIB dependency search directory is valid. Fail if not.
        if not os.path.exists(self.options.mibdepsdir):
            self.log.error(
                "'mibdepsdir' path not found: %s", self.options.mibdepsdir
            )
            sys.exit(1)

        if self.options.keeppythoncode:
            path = self.options.pythoncodedir
            if not os.path.exists(path):
                self.log.error("Python code dir not found: %s", path)
                sys.exit(1)
            if not os.path.isdir(path):
                self.log.error("Python code dir is not a directory: %s", path)
                sys.exit(1)

        # Verify that the target MIB organizer exists
        miborgpath = os.path.join("/zport/dmd/Mibs", self.options.path)
        miborg = self.dmd.unrestrictedTraverse(miborgpath, None)
        if miborg is None:
            self.log.error(
                "MIB organizer path option ('path') not found: %s",
                self.options.path
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
            '--path', dest='path', default="",
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
    zm.run()
