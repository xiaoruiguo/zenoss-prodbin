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

from subprocess import PIPE
from unittest import TestCase

from Products.ZenUtils.Utils import zenPath
from Products.ZenUtils.mib import SMIConfigFile, SMIDump, SMIDumpTool, MIBFile
from Products.ZenUtils.mib import smidump


def _readfile(path):
    with open(path, 'r') as fd:
        return fd.read()


class TestSMIConfigFile(TestCase):

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


class TestSMIDump(TestCase):

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

        dump_data = _readfile(dump_fname)
        expected_def = _readfile(defs_fname).strip()  # remove trailing \n

        dump = SMIDump(dump_data)

        defs = list(dump.definitions)
        self.assertEqual(len(defs), 1)
        self.assertMultiLineEqual(defs[0], expected_def)

    def test_two_modules(self):
        basePath = zenPath("Products/ZenUtils/mib/tests")
        dump_fname = os.path.join(basePath, "two_modules.mib.py")
        defs1_fname = os.path.join(basePath, "SMIDUMP01-MIB.mib.defn")
        defs2_fname = os.path.join(basePath, "SMIDUMP02-MIB.mib.defn")

        dump_data = _readfile(dump_fname)
        expected_def1 = _readfile(defs1_fname).strip()  # remove trailing \n
        expected_def2 = _readfile(defs2_fname).strip()  # remove trailing \n

        dump = SMIDump(dump_data)

        defs = list(dump.definitions)
        self.assertEqual(len(defs), 2)
        self.assertMultiLineEqual(defs[0], expected_def1)
        self.assertMultiLineEqual(defs[1], expected_def2)

    def test_one_file(self):
        basePath = zenPath("Products/ZenUtils/mib/tests")
        dump_fname = os.path.join(basePath, "SMIDUMP01-MIB.mib.py")
        dump_data = _readfile(dump_fname)
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

        dump_data = _readfile(dump_fname)
        expected_file1 = _readfile(file1_fname)
        expected_file2 = _readfile(file2_fname)

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

        dump_data = _readfile(dump_fname)
        expected_file1 = _readfile(file1_fname)
        expected_file2 = _readfile(file2_fname)

        dump = SMIDump(dump_data)

        files = list(dump.files)
        self.assertEqual(len(files), 2)

        item = next((i for i in files if i[0] == "multi.mib"), None)
        self.assertIsNotNone(item)
        self.assertMultiLineEqual(item[1], expected_file1)

        item = next((i for i in files if i[0] == "SMIDUMP03-MIB.mib"), None)
        self.assertIsNotNone(item)
        self.assertMultiLineEqual(item[1], expected_file2)


class TestSMIDumpTool(TestCase):

    @mock.patch("Products.ZenUtils.mib.smidump.Popen")
    def test_cmdline_no_config(self, mockPopen):
        mockProcess = mock.Mock(spec=smidump.Popen)
        mockPopen.return_value = mockProcess
        mockProcess.communicate = mock.Mock(return_value=([""], [""]))
        mockProcess.poll = mock.Mock(return_value=0)

        mockMibFile = mock.Mock(spec=MIBFile)
        mockMibFile.filename = "FAKE-MIB.mib"
        mockMibFile.names = ["FAKE-MIB"]

        expected_cmd = [
            "smidump", "--keep-going", "--format", "python", "FAKE-MIB.mib"
        ]

        tool = SMIDumpTool()
        dump = tool.run(mockMibFile)
        self.assertIsInstance(dump, SMIDump)
        self.assertEqual(len(list(dump.definitions)), 0)
        mockPopen.assert_called_once_with(
            expected_cmd, stdout=PIPE, stderr=PIPE, close_fds=True
        )

    @mock.patch("Products.ZenUtils.mib.smidump.Popen")
    @mock.patch("Products.ZenUtils.mib.tests.test_smidump.SMIConfigFile")
    def test_cmdline_with_config(self, mockConfig, mockPopen):
        mockProcess = mock.Mock(spec=smidump.Popen)
        mockPopen.return_value = mockProcess
        mockProcess.communicate = mock.Mock(return_value=([""], [""]))
        mockProcess.poll = mock.Mock(return_value=0)

        mockConfig.filename = "tempfile.conf"
        mockConfig.__enter__.return_value = mockConfig

        mockMibFile = mock.Mock(spec=MIBFile)
        mockMibFile.filename = "FAKE-MIB.mib"
        mockMibFile.names = ["FAKE-MIB"]

        expected_cmd = [
            "smidump", "--keep-going", "--format", "python",
            "--config", "tempfile.conf", "FAKE-MIB.mib"
        ]

        with mockConfig as cfg:
            tool = SMIDumpTool(config=cfg)
            dump = tool.run(mockMibFile)

        self.assertIsInstance(dump, SMIDump)
        self.assertEqual(len(list(dump.definitions)), 0)
        mockPopen.assert_called_once_with(
            expected_cmd, stdout=PIPE, stderr=PIPE, close_fds=True
        )

    @mock.patch("Products.ZenUtils.mib.smidump.Popen")
    def test_cmdline_n_files(self, mockPopen):
        mockProcess = mock.Mock(spec=smidump.Popen)
        mockPopen.return_value = mockProcess
        mockProcess.communicate = mock.Mock(return_value=([""], [""]))
        mockProcess.poll = mock.Mock(return_value=0)

        mockMibFile1 = mock.Mock(spec=MIBFile)
        mockMibFile1.filename = "FAKE-01-MIB.mib"
        mockMibFile1.names = ["FAKE-01-MIB"]
        mockMibFile2 = mock.Mock(spec=MIBFile)
        mockMibFile2.filename = "FAKE-02-MIB.mib"
        mockMibFile2.names = ["FAKE-02-MIB"]

        expected_cmd = [
            "smidump", "--keep-going", "--format", "python",
            "FAKE-01-MIB.mib", "FAKE-02-MIB.mib"
        ]

        tool = SMIDumpTool()
        dump = tool.run(mockMibFile1, mockMibFile2)
        self.assertIsInstance(dump, SMIDump)
        self.assertEqual(len(list(dump.definitions)), 0)
        mockPopen.assert_called_once_with(
            expected_cmd, stdout=PIPE, stderr=PIPE, close_fds=True
        )

    @mock.patch("Products.ZenUtils.mib.smidump.Popen")
    def test_cmdline_one_file_n_modules(self, mockPopen):
        mockProcess = mock.Mock(spec=smidump.Popen)
        mockPopen.return_value = mockProcess
        mockProcess.communicate = mock.Mock(return_value=([""], [""]))
        mockProcess.poll = mock.Mock(return_value=0)

        mockMibFile = mock.Mock(spec=MIBFile)
        mockMibFile.filename = "FAKE-01-MIB.mib"
        mockMibFile.names = ["FAKE-01-MIB", "FAKE-02-MIB", "FAKE-03-MIB"]

        expected_cmd = [
            "smidump", "--keep-going", "--format", "python",
            "FAKE-01-MIB.mib", "FAKE-01-MIB", "FAKE-02-MIB"
        ]

        tool = SMIDumpTool()
        dump = tool.run(mockMibFile)
        self.assertIsInstance(dump, SMIDump)
        self.assertEqual(len(list(dump.definitions)), 0)
        mockPopen.assert_called_once_with(
            expected_cmd, stdout=PIPE, stderr=PIPE, close_fds=True
        )

    @mock.patch("Products.ZenUtils.mib.smidump.Popen")
    def test_cmdline_n_files_n_modules(self, mockPopen):
        mockProcess = mock.Mock(spec=smidump.Popen)
        mockPopen.return_value = mockProcess
        mockProcess.communicate = mock.Mock(return_value=([""], [""]))
        mockProcess.poll = mock.Mock(return_value=0)

        mockMibFile1 = mock.Mock(spec=MIBFile)
        mockMibFile1.filename = "fake001.txt"
        mockMibFile1.names = ["FAKE-01-MIB", "FAKE-02-MIB"]
        mockMibFile2 = mock.Mock(spec=MIBFile)
        mockMibFile2.filename = "fake002.txt"
        mockMibFile2.names = ["MOCK-MIB", "PSUEDO-MIB", "FLIMFLAM-MIB"]

        expected_cmd = [
            "smidump", "--keep-going", "--format", "python",
            "fake001.txt", "fake002.txt",
            "FAKE-01-MIB", "MOCK-MIB", "PSUEDO-MIB"
        ]

        tool = SMIDumpTool()
        dump = tool.run(mockMibFile1, mockMibFile2)
        self.assertIsInstance(dump, SMIDump)
        self.assertEqual(len(list(dump.definitions)), 0)
        mockPopen.assert_called_once_with(
            expected_cmd, stdout=PIPE, stderr=PIPE, close_fds=True
        )

    @mock.patch("Products.ZenUtils.mib.smidump.Popen")
    def test_cmd_error(self, mockPopen):
        mockProcess = mock.Mock(spec=smidump.Popen)
        mockPopen.return_value = mockProcess
        mockProcess.communicate = mock.Mock(return_value=([""], ["boom"]))
        mockProcess.poll = mock.Mock(return_value=128)

        mockMibFile = mock.Mock(spec=MIBFile)
        mockMibFile.filename = "fake001.txt"
        mockMibFile.names = ["FAKE-01-MIB"]

        tool = SMIDumpTool()
        with self.assertRaises(RuntimeError) as ex:
            tool.run(mockMibFile)
        self.assertMultiLineEqual(str(ex.exception), "smidump failed:\nboom")
