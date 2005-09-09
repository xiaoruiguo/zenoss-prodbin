"""A minimalistic syslogd.

2000-06-09/bb:  created
2000-06-12/bb:  added constants from syslog.h,
                config options for time format, stop string
"""

import sys, string, time, socket, re
from SocketServer import *

# constants from syslog.h
LOG_EMERG       = 0
LOG_ALERT       = 1
LOG_CRIT        = 2
LOG_ERR         = 3
LOG_WARNING     = 4
LOG_NOTICE      = 5
LOG_INFO        = 6
LOG_DEBUG       = 7

LOG_PRIMASK     = 0x07

def LOG_PRI(p): return p & LOG_PRIMASK
def LOG_MAKEPRI(fac, pri): return fac << 3 | pri

LOG_KERN        = 0 << 3
LOG_USER        = 1 << 3
LOG_MAIL        = 2 << 3
LOG_DAEMON      = 3 << 3
LOG_AUTH        = 4 << 3
LOG_SYSLOG      = 5 << 3
LOG_LPR         = 6 << 3
LOG_NEWS        = 7 << 3
LOG_UUCP        = 8 << 3
LOG_CRON        = 9 << 3
LOG_AUTHPRIV    = 10 << 3
LOG_FTP         = 11 << 3
LOG_LOCAL0      = 16 << 3
LOG_LOCAL1      = 17 << 3
LOG_LOCAL2      = 18 << 3
LOG_LOCAL3      = 19 << 3
LOG_LOCAL4      = 20 << 3
LOG_LOCAL5      = 21 << 3
LOG_LOCAL6      = 22 << 3
LOG_LOCAL7      = 23 << 3

LOG_NFACILITIES = 24
LOG_FACMASK     = 0x03F8
def LOG_FAC(p): return (p & LOG_FACMASK) >> 3

def LOG_MASK(pri): return 1 << pri
def LOG_UPTO(pri): return (1 << pri + 1) - 1
# end syslog.h

def LOG_UNPACK(p): return (p & LOG_FACMASK, LOG_PRI(p))

fac_values = {}     # mapping of facility constants to their values
fac_names = {}      # mapping of values to names
pri_values = {}
pri_names = {}
for i, j in globals().items():
    if i[:4] == 'LOG_' and type(j) == type(0):
        if j > LOG_PRIMASK or i == 'LOG_KERN':
            n, v = fac_names, fac_values
        else:
            n, v = pri_names, pri_values
        i = i[4:].lower()
        v[i] = j
        n[j] = i
del i, j, n, v


conf_pat = re.compile(r'''
    ^\s*            # leading space
    ([\w*]+)        # facility
    \.([=!]?)       # separator plus optional modifier
    ([\w*]+)        # priority
    \s+
    ([|@]?)         # target type fifo/remote host
    (\S+)           # target
    ''', re.VERBOSE)


class InterruptibleServer:
    "Mix-in class for {TCP,UDP}Server that allows to stop the service"

    def serve(self):
        "Run the service until it is stopped with the stop() method."
        self.running = 1
        while self.running:
            try:
                self.handle_request()
            except KeyboardInterrupt:
                self.stop()

    def stop(self):             # called by handle_request()
        "Stop the service."
        self.running = 0


SYSLOG_PORT = socket.getservbyname('syslog', 'udp')

class Syslogd(ThreadingUDPServer, InterruptibleServer):

    def __init__(self, addr='', port=SYSLOG_PORT, pri=LOG_DEBUG, timefmt=None, magic=None):

        UDPServer.__init__(self, (addr, port), None)

        self.hostmap = {}       # client address/name mapping
        self.priority = pri
        self.timefmt = timefmt or '%b %d %H:%M:%S'
        self.stop_magic = magic or '_stop'

        print 'syslogd started'

    def finish_request(self, (msg, sock), client_address):

        # get the time when the message arrives
        tm = time.time()

        # Messages are in the form "[[float]]<int>message text...\n"
        # The [[float]] and <int> parts and the newline are optional.
        # The float denotes the original event time in case the
        # event comes through a gateway from a client that is not
        # syslog-compatible (Windows NT comes to mind :-).

        # extract original event time, if present
        if msg[:2] == '[[':
            pos = msg.find(']]')
            try:
                tm = float(msg[2:pos])
            except:
                pass
            msg = msg[pos+2:]   # use rest of message

        # extract log facility and priority, if present
        if msg[:1] == '<':
            pos = msg.find('>')
            fac, pri = LOG_UNPACK(int(msg[1:pos]))
            msg = msg[pos+1:]
        elif msg and msg[0] < ' ':
            fac, pri = LOG_KERN, ord(msg[0])
            msg = msg[1:]
        else:
            fac, pri = None, None

        # check if we can discard this message
        if pri is not None and pri > self.priority:
            return

        # build the client address/name mapping
        client = client_address[0]
        try:
            host = self.hostmap[client]
        except KeyError:
            try:
                host = socket.gethostbyaddr(client)[0]
                host = host.split('.')[0]       # keep only the host name
            except socket.error:
                host = client
            self.hostmap[client] = host

        # print the message
        tm = time.strftime(self.timefmt, time.localtime(tm))
        if 0: # fac is not None and pri is not None:
            fp = ' <%s,%s>' % (fac_names[fac], pri_names[pri])
        else:
            fp = ''
        sys.stdout.write(tm + ' ' + host + fp + ': ' + msg.strip() + '\n')

        # stop the server if the magic stop string appears in the message
        if msg.find(self.stop_magic) >= 0:
            print 'stopped.'
            self.stop()


if __name__ == '__main__':
    Syslogd(timefmt='%H:%M:%S').serve()

