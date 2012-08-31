#!/usr/bin/python
# vim: set expandtab:
# vim: set tabstop=4:
# vim: set autoindent:

import sys

# Abstract base class.
class Command():
    def handle(self, conn, args):
        pass

# Reset command.
class ResetCommand(Command):
    def handle(self, conn, args):
        if (raw_input("Are you sure you want to reset the database? [y/N] ").lower() != "y"):
            print "Not doing anything."
            return
        print "Resetting database..."
        c = conn.cursor()

        # Delete existing tables.
        for r in c.execute("SELECT name FROM sqlite_master"):
            c.execute("DROP TABLE %s", r)

        # Recreate new tables.
        c.execute("""
CREATE TABLE computers
(
    ip TEXT,
    network_id INTEGER,
    hostname TEXT,
    person TEXT
);

CREATE TABLE networks
(
    interface TEXT
);

CREATE TABLE quotas
(
    computer_id INTEGER,
    network_id INTEGER,
    period INTEGER,
    quota INTEGER
);

CREATE TABLE usage
(
    computer_id INTEGER,
    quota_id INTEGER,
    end_time INTEGER,
    bytes INTEGER
);
""")
        conn.commit()
        c.close()

# Network command.
class NetworkCommand(Command):
    def handle(self, conn, args):
        if (len(args) == 0):
            print "list - List all networks."
            print "add <interface> - Add a new network on the specified interface."
            print "remove <interface> - Remove a network by interface."
        elif (args[0].lower() == "list" and len(args) == 1):
            c = conn.cursor()
            results = c.execute("SELECT interface FROM networks")
            print len(results) + " networks configured."
            for i in results:
                print " - " + i
            c.close()
        elif (args[0].lower() == "add" and len(args) == 2):
            c = conn.cursor()
            if (len(c.execute("SELECT interface FROM networks WHERE interface = '%s'", args[1])) > 0):
                print "A network already exists on interface " + args[1] + "."
                return
            if (c.execute("INSERT INTO networks (interface) VALUES ('%s')", args[1])):
                print "Added network on interface " + args[1] + "."
            else:
                print "Failed to add network on interface " + args[1] + "."
            conn.commit()
            c.close()

# Help command.
class HelpCommand(Command):
    def handle(self, conn, args):
        print "reset - Clears and recreates the database."
        print "network - Control networks."
        print "computer - Control computers."
        print "quota - Control quotas."
        print "usage - Display and examine usage."
        print "help - This help."
        print "quit - Quits the control program."
