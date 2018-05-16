import os
import re
import tarfile
import urllib
import zipfile

from urlparse import urlsplit, SplitResult

moduleNameMatcher = re.compile(
    r"([A-Z][a-zA-Z0-9-_]+)\s+DEFINITIONS\s+.*?\s*::=\s*BEGIN.+?END", re.DOTALL
)

__all__ = ("MIBFile", "PackageManager", "Package")


class MIBFile(object):
    """A MIB file may contain one or more MIB module definitions.

    This class wraps an open file object and reads its contents.  It will
    not close the file nor write to the file.
    """

    def __init__(self, filename, contents):
        """Initialize an instance of MIBFile.

        @param filename {string} Name of the file containing MIB definitions.
        @param contents {string} Contents of the named file.
        """
        self._filename = filename
        names = tuple(moduleNameMatcher.findall(contents))
        if not names:
            raise ValueError("No MIB definitions found in content")
        self._names = names
        self._reprstr = "<%s %s, definition%s %s>" % (
            self.__class__.__name__, self._filename,
            "" if len(self._names) == 1 else "s", ", ".join(self._names)
        )
        self.__hash = hash(self._filename)

    @property
    def filename(self):
        return self._filename

    @property
    def module_names(self):
        """A tuple containing the name of each module definition found
        in the file.
        """
        return self._names

    def __eq__(self, other):
        if type(self) != type(other):
            return NotImplemented
        return self._filename == other._filename

    def __ne__(self, other):
        if type(self) != type(other):
            return NotImplemented
        return self._filename != other._filename

    def __hash__(self):
        return self.__hash

    def __repr__(self):
        self._reprstr

    def __str__(self):
        return self._filename


def _pathwalker(root):
    """A generator that returns each file in the path given by root.
    """
    for path, _, filenames in os.walk(root):
        for name in filenames:
            yield os.path(path, name)


def _removeDirContents(path):
    for root, dirs, files in os.walk(path, topdown=False):
        if root == os.sep:  # Should *never* get here
            break
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            try:
                os.removedirs(os.path.join(root, name))
            except OSError:
                pass


class PRL(object):
    """A PRL is a Package Resource Locator.

    Basically a URL specialized to work with PackageManager.
    """

    def __init__(self, url):
        """
        """
        # urlsplit will parse what it can from the provided string.
        raw = urlsplit(url)

        if not raw.path:
            raise ValueError("Invalid argument for MIB source: %s" % url)

        scheme = raw.scheme
        if not scheme:
            scheme = "file" if not raw.netloc else "http"

        path = raw.path
        if scheme == "file" and not path.startswith("/"):
            path = os.path.abspath("./" + path)

        cooked = SplitResult(scheme, raw.netloc, path, raw.query, raw.fragment)
        self._url = cooked.geturl()
        self._scheme = scheme
        self._filename = os.path.split(cooked.path)[-1]

    @property
    def url(self):
        """The URL of the package."""
        return self._url

    @property
    def scheme(self):
        """The scheme of the package's URL."""
        return self._scheme

    @property
    def filename(self):
        """The package's filename."""
        return self._filename


class ZipExtractor(object):

    def challenge(self, source):
        return zipfile.is_zipfile(source)

    def extract(self, source, path):
        """Unzip the source file into the given directory path.
        """
        with zipfile.ZipFile(source, 'r') as zf:
            if zf.testzip() is not None:
                raise ValueError("Zip file %s is corrupted" % source)
            zf.extractall(path)


class TarExtractor(object):

    def challenge(self, source):
        return tarfile.is_tarfile(source)

    def extract(self, source, path):
        """Extract the source tar file into the target directory.
        """
        with tarfile.open(source, 'r') as tf:
            for info in (mi for mi in tf if mi.isfile()):
                self._write(tf, info, path)

    def _write(self, tf, info, path):
        dirname, filename = os.path.split(info.name)
        targetdir = os.path.join(path, dirname)
        if not os.path.exists(targetdir):
            os.mkdir(targetdir)
        elif not os.path.isdir(targetdir):
            raise ValueError(
                "Unable to extract %s; target path, %s, "
                "is not a directory" % (info.name, targetdir)
            )
        targetfile = os.path.join(targetdir, filename)
        with tf.extractfile(info) as src, open(targetfile, 'w') as sink:
            sink.write(src.read())


class DirectoryExtractor(object):

    def challenge(self, source):
        return os.path.isdir(source)

    def extract(self, source, path):
        """
        """
        return list(_pathwalker(source))


class FileExtractor(object):

    def extract(self, source, path):
        """
        """
        return [source]


_extractors = [ZipExtractor(), TarExtractor(), DirectoryExtractor()]
_fileExtractor = FileExtractor()


class Package(object):

    @classmethod
    def make(cls, source, target):
        """
        """
        for extractor in _extractors:
            if extractor.challenge(source):
                return cls(extractor, source, target)
        else:
            return cls(_fileExtractor, source, target)

    def __init__(self, extractor, source, target):
        """
        """
        self._extractor = extractor
        self._source = source
        self._target = target

    def extract(self):
        """Extracts the package, returns a list of MIBFiles representing
        the files found in the package.
        """
        files = self._extractor.extract(self._source, self._target)
        mibfiles = []
        for pkgfile in files:
            with open(pkgfile, 'r') as f:
                contents = f.read()
                mibfiles.append(MIBFile(pkgfile, contents))
        return mibfiles


class PackageManager(object):
    """
    Given an URL, filename or archive (eg zip, tar), extract the files from
    the package and return a list of filenames.
    """

    def __init__(self, log, downloaddir, extractdir):
        """
        Initialize the packagae manager.

        @parameter log: logging object
        @type log: logging class object
        @parameter downloaddir: directory name to store downloads
        @type downloaddir: string
        @parameter extractdir: directory name to store downloads
        @type extractdir: string
        """
        self.log = log
        self._downloaddir = downloaddir
        self._extractdir = extractdir

    def get(self, source):
        """Return the given source as a Package object.
        """
        prl = PRL(source)
        if prl.scheme != "file":
            # A remote file will not have a 'file' scheme; so retrieve it.
            filepath, _ = urllib.urlretrieve(prl.url, self._downloaddir)
            prl = PRL(filepath)

        return Package.make(prl.filename, self._extractdir)

    def cleanup(self):
        """
        Remove any clutter left over from the installation.
        """
        _removeDirContents(self._downloaddir)
        _removeDirContents(self._extractdir)
