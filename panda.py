
import sys
import getopt
import pandaui

def show_help():
    sys.exit("Usage: %s <options>\n\n"
             "Options:\n"
             " -p --port     Port to connect to\n"
             " -n --nick     Specify nickname to use\n"
             " -c --connect  Autoconnect to server given\n"
             " -h --help     Show this help information" % sys.argv[0])

if __name__ == "__main__":
    port = 6667
    nick = "pandairc"
    srv  = None
    opts, args = getopt.getopt(sys.argv[1:], "p:n:c:h",
                               ["port=", "nick=", "connect=",
                                "help"])
    for i in opts:
        opt, value = i
        if opt == "-p" or opt == "--port":
            port = value
        elif opt == "-n" or opt == "--nick":
            nick = value
        elif opt == "-c" or opt == "--connect":
            srv = value
        elif opt == "-h" or opt == "--help":
            show_help()
    pandaui.PandaUI(port, nick, srv)