##############################################################################
#
# Copyright (C) Zenoss, Inc. 2018, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import mock
import os

from Products.ZenTestCase.BaseTestCase import BaseTestCase
from Products.ZenUtils.Utils import zenPath

from Products.ZenUtils.mib import SMIConfigFile, SMIDump  # , SMIDumpTool
from Products.ZenUtils.mib import smidump


class TestSMIConfigFile(BaseTestCase):

    def test_nopath(self):
        tempFile = mock.Mock()
        tempFile.name = "tempfile"
        fakeTempFileFactory = mock.Mock(return_value=tempFile)
        orig = smidump.NamedTemporaryFile
        try:
            smidump.NamedTemporaryFile = fakeTempFileFactory
            with SMIConfigFile() as cfg:
                self.assertEqual(cfg.filename, "tempfile")
                tempFile.write.assert_called_with("path :\n")
                self.assertTrue(tempFile.flush.called)
            self.assertTrue(tempFile.close.called)
        finally:
            smidump.NamedTemporaryFile = orig

    def test_onepath(self):
        tempFile = mock.Mock()
        tempFile.name = "tempfile"
        fakeTempFileFactory = mock.Mock(return_value=tempFile)
        orig = smidump.NamedTemporaryFile
        path = ["/opt/zenoss/share/mibs"]
        try:
            smidump.NamedTemporaryFile = fakeTempFileFactory
            with SMIConfigFile(path=path) as cfg:
                self.assertEqual(cfg.filename, "tempfile")
                tempFile.write.assert_called_with(
                    "path :/opt/zenoss/share/mibs\n"
                )
        finally:
            smidump.NamedTemporaryFile = orig

    def test_multiple_paths(self):
        tempFile = mock.Mock()
        tempFile.name = "tempfile"
        fakeTempFileFactory = mock.Mock(return_value=tempFile)
        orig = smidump.NamedTemporaryFile
        path = ["/opt/zenoss/share/mibs", "/a/b/c", "/x/y/z"]
        try:
            smidump.NamedTemporaryFile = fakeTempFileFactory
            with SMIConfigFile(path=path) as cfg:
                self.assertEqual(cfg.filename, "tempfile")
                tempFile.write.assert_called_with(
                    "path :%s\n" % ':'.join(path)
                )
        finally:
            smidump.NamedTemporaryFile = orig


class TestSMIDump(BaseTestCase):

    def setUp(self):
        self.maxDiff = None

    def test_empty(self):
        dump = SMIDump("")
        self.assertEqual(list(dump.definitions), [])
        self.assertEqual(list(dump.files), [])

    def test_one_module(self):
        basePath = zenPath("Products/ZenUtils/mib/tests")
        dump_fname = os.path.join(basePath, "SMIDUMP01-MIB.mib.py")
        defs_fname = os.path.join(basePath, "SMIDUMP01-MIB.mib.defn")

        dump_data = open(dump_fname).read()
        expected_def = open(defs_fname).read().strip()  # remove trailing \n

        dump = SMIDump(dump_data)

        defs = list(dump.definitions)
        self.assertEqual(len(defs), 1)
        self.assertMultiLineEqual(defs[0], expected_def)

    def test_two_modules(self):
        basePath = zenPath("Products/ZenUtils/mib/tests")
        dump_fname = os.path.join(basePath, "two_modules.mib.py")
        defs1_fname = os.path.join(basePath, "SMIDUMP01-MIB.mib.defn")
        defs2_fname = os.path.join(basePath, "SMIDUMP02-MIB.mib.defn")

        dump_data = open(dump_fname).read()
        expected_def1 = open(defs1_fname).read().strip()  # remove trailing \n
        expected_def2 = open(defs2_fname).read().strip()  # remove trailing \n

        dump = SMIDump(dump_data)

        defs = list(dump.definitions)
        self.assertEqual(len(defs), 2)
        self.assertMultiLineEqual(defs[0], expected_def1)
        self.assertMultiLineEqual(defs[1], expected_def2)

    def test_one_file(self):
        basePath = zenPath("Products/ZenUtils/mib/tests")
        dump_fname = os.path.join(basePath, "SMIDUMP01-MIB.mib.py")
        dump_data = open(dump_fname).read()
        dump = SMIDump(dump_data)

        files = list(dump.files)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0][0], "SMIDUMP01-MIB.mib")
        self.assertMultiLineEqual(files[0][1], dump_data)

    def test_two_files(self):
        basePath = zenPath("Products/ZenUtils/mib/tests")
        dump_fname = os.path.join(basePath, "two_modules.mib.py")
        file1_fname = os.path.join(basePath, "SMIDUMP01-MIB.mib.py")
        file2_fname = os.path.join(basePath, "SMIDUMP02-MIB.mib.py")

        dump_data = open(dump_fname).read()
        expected_file1 = open(file1_fname).read()
        expected_file2 = open(file2_fname).read()

        dump = SMIDump(dump_data)

        files = list(dump.files)
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0][0], "SMIDUMP01-MIB.mib")
        self.assertMultiLineEqual(files[0][1], expected_file1)
        self.assertEqual(files[1][0], "SMIDUMP02-MIB.mib")
        self.assertMultiLineEqual(files[1][1], expected_file2)

    def test_two_files_three_modules(self):
        basePath = zenPath("Products/ZenUtils/mib/tests")
        dump_fname = os.path.join(basePath, "three_modules.py")
        file1_fname = os.path.join(basePath, "multi.mib.py")
        file2_fname = os.path.join(basePath, "SMIDUMP03-MIB.mib.py")

        dump_data = open(dump_fname).read()
        expected_file1 = open(file1_fname).read()
        expected_file2 = open(file2_fname).read()

        dump = SMIDump(dump_data)

        files = list(dump.files)
        self.assertEqual(len(files), 2)

        item = next((i for i in files if i[0] == "multi.mib"), None)
        self.assertIsNotNone(item)
        self.assertMultiLineEqual(item[1], expected_file1)

        item = next((i for i in files if i[0] == "SMIDUMP03-MIB.mib"), None)
        self.assertIsNotNone(item)
        self.assertMultiLineEqual(item[1], expected_file2)
