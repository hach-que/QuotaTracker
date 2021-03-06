#!/usr/bin/python
# vim: set expandtab:
# vim: set tabstop=4:
# vim: set autoindent:

import sys
import time

# Abstract base class.
class Command():
    def handle(self, conn, c, args):
        pass

# Reset command.
class ResetCommand(Command):
    def handle(self, conn, c, args):
        if (raw_input("Are you sure you want to reset the database? [y/N] ").lower() != "y"):
            print "Not doing anything."
            return

        # Delete existing tables.
        delete = list()
        for r in c.execute("SELECT name FROM sqlite_master"):
            delete.append(r[0])
        for r in delete:
            print "Erasing %s.." % r
            c.execute("DROP TABLE " + r)
        conn.commit()

        # Recreate new tables.
        print "Recreating tables..."
        c.execute("""
            CREATE TABLE computers
            (
                hostname TEXT,
                person TEXT,
                period INTEGER,
                quota INTEGER,
                use_tor BOOLEAN
            )""")
        c.execute("""
            CREATE TABLE usage
            (
                computer_id INTEGER,
                end_time INTEGER,
                bytes INTEGER
            )""")
        c.execute("""
            CREATE TABLE port
            (
                computer_id INTEGER,
                ports TEXT
            )""")
        conn.commit()

# Computer command.
class ComputerCommand(Command):
    def handle(self, conn, c, args):
        if (len(args) == 0 or args[0].lower() == "help"):
            print "list - List all computers."
            print "add <hostname> <person> - Add a new computer mapping on the specified interface."
            print "delete <hostname> - Remove a computer by interface and hostname."
        elif (args[0].lower() == "list" and len(args) == 1):
            results = list()
            for i in c.execute("SELECT hostname, person, use_tor FROM computers"):
                results.append(i)
            print "%i computers configured." % len(results)
            for i in results:
                if i[2]:
                    print " - %s (%s) VIA TOR" % (i[0], i[1])
                else:
                    print " - %s (%s)" % (i[0], i[1])                  
        elif (args[0].lower() == "add" and len(args) == 3):
            hostname = args[1].lower()
            person = args[2]
            c.execute("SELECT COUNT(hostname) FROM computers WHERE LOWER(hostname) = ?", (hostname,))
            if (c.fetchone()[0] > 0):
                print "A computer already exists with hostname %s." % hostname
                return
            if (c.execute("INSERT INTO computers (hostname, person, period, quota, use_tor) VALUES (LOWER(?), ?, ?, ?, ?)", (hostname, person, 0, 0, False))):
                print "Added computer %s (%s)." % (hostname, person)
                print "Assigned computer %s a quota of 0 bytes over 0 seconds."
            else:
                print "Failed to add computer %s." % hostname
                return
            conn.commit()
        elif (args[0].lower() == "delete" and len(args) == 2):
            hostname = args[1].lower()
            c.execute("SELECT COUNT(hostname) FROM computers WHERE LOWER(hostname) = ?", (hostname,))
            if (c.fetchone()[0] == 0):
                print "No computer %s exists." % hostname
                return
            if (c.execute("DELETE FROM computers WHERE LOWER(hostname) = ?", (hostname,))):
                print "Deleted computer %s." % hostname
            else:
                print "Failed to delete computer %s." % hostname
            conn.commit()
        else:
            print "Invalid number of arguments."

# Tor command.
class TorCommand(Command):
    def handle(self, conn, c, args):
        if (len(args) == 0 or args[0].lower() == "help"):
            print "list - Show status of Tor on computers."
            print "on <hostname> - Turn transparent Tor on for the specified hostname."
            print "off <hostname> - Turn transparent Tor off for the specified hostname."
        elif (args[0].lower() == "list" and len(args) == 1):
            tor_on = list()
            tor_off = list()
            for i in c.execute("SELECT hostname, person, use_tor FROM computers"):
                if i[2]:
                    tor_on.append(i)
                else:
                    tor_off.append(i)
            print "%i computers using Tor:" % len(tor_on)
            for i in tor_on:
                print " - %s (%s)" % (i[0], i[1])
            print "%i computers not using Tor:" % len(tor_off)
            for i in tor_off:
                print " - %s (%s)" % (i[0], i[1])
        elif (args[0].lower() == "on" and len(args) == 2):
            hostname = args[1].lower()
            print "Enabled transparent Tor for %s." % hostname
            print "Verify by accessing https://check.torproject.org/ from the machine."
            print "It might take a minute for the changes to apply."
            c.execute("UPDATE computers SET use_tor = ? WHERE LOWER(hostname) = ?", (True, hostname))
            conn.commit()
        elif (args[0].lower() == "off" and len(args) == 2):
            hostname = args[1].lower()
            print "Disabled transparent Tor for %s." % hostname
            print "It might take a minute for the changes to apply."
            c.execute("UPDATE computers SET use_tor = ? WHERE LOWER(hostname) = ?", (False, hostname))
            conn.commit()

# Quota command.
class QuotaCommand(Command):
    def handle(self, conn, c, args):
        if (len(args) == 0 or args[0].lower() == "help"):
            print "list - Show quotas assigned to computers."
            print "set <period> <amount> - Set quotas for all computers."
            print "set <hostname> <period> <amount> - Set quota for a single computer specified by hostname."
            print "reset - Reset the quota timers, forcing a new quota cycle to begin."
        elif (args[0].lower() == "list" and len(args) == 1):
            results = list()
            for i in c.execute("SELECT hostname, period, quota FROM computers"):
                results.append(i)
            print "%i computers configured." % len(results)
            for i in results:
                print " - %s (%i secs) (%i bytes)" % (i[0], i[1], i[2])
        elif (args[0].lower() == "set" and len(args) == 3):
            period = int(args[1])
            quota = int(args[2])
            print "Assigned all computers a quota of %i bytes over %i seconds." % (quota, period)
            c.execute("UPDATE computers SET period = ?, quota = ?", (period, quota))
            conn.commit()
        elif (args[0].lower() == "set" and len(args) == 4):
            hostname = args[1].lower()
            period = int(args[2])
            quota = int(args[3])
            print "Assigned %s a quota of %i bytes over %i seconds." % (hostname, quota, period)
            c.execute("UPDATE computers SET period = ?, quota = ? WHERE LOWER(hostname) = ?", (period, quota, hostname))
            conn.commit()
        elif (args[0].lower() == "reset" and len(args) == 1):
            c.execute("UPDATE usage SET end_time = ? WHERE end_time > ?", (time.time(), time.time()))
            conn.commit()
            print "Reset all quota timers and archived existing usage."

# Ports command.
class PortsCommand(Command):
    def handle(self, conn, c, args):
        if (len(args) == 0 or args[0].lower() == "help"):
            print "list - Show list of blocking outgoing and incoming ports."
            print "block <hostname> <ports> - Block a port or series of ports for a computer."
            print "unblock <hostname> <ports> - Unblock ports for a computer."
            print "Ports can be specified as a single port like 5600, or a range of ports"
            print "in the form of 5000-6000."
        elif (args[0].lower() == "list"):
            computers = list()
            at_least_one = False
            for i in c.execute("SELECT rowid, hostname FROM computers"):
                computers.append((i[0], i[1]));
            for i in computers:
                ports = list()
                for a in c.execute("SELECT ports FROM ports WHERE computer_id = ?", (i[0],)):
                    ports.append(a)
                if len(ports) > 0:
                    at_least_one = True
                    print "%s has the following ports blocked:" % (i[1])
                    for z in ports:
                        print " - %s" % (z)
            if at_least_one:
                print "All other computers have no ports blocked."
            else:
                print "No computers have ports blocked."
        elif (args[0].lower() == "block" and len(args[0]) > 2):
            computers = list()
            at_least_one = False
            for i in c.execute("SELECT rowid, hostname FROM computers WHERE LOWER(hostname) = ?", (args[1],)):
                computers.append((i[0], i[1]));
            if len(computers) == 0:
                print "No such hostname."
                return
            elif len(computers) != 1:
                print "Hostname is ambigious."
                return
            computer = computers[0]
            for i in args[2:]:
                if (i.find('-') == -1):
                    try:
                        p = int(i)
                        c.execute("INSERT INTO ports (computer_id, ports) VALUES (?, ?)", (computer[0], str(p)))
                        conn.commit()
                    except:
                        print "Invalid port specifier \"%s\"" % i
                else:
                    try:
                        start = int(i.split('-', 2)[0])
                        end = int(i.split('-', 2)[1])
                        c.execute("INSERT INTO ports (computer_id, ports) VALUES (?, ?)", (computer[0], str(start) + "-" + str(end)))
                        conn.commit()
                    except:
                        print "Invalid port specifier \"%s\"" % i
        elif (args[0].lower() == "unblock" and len(args[0]) > 2):
            computers = list()
            at_least_one = False
            for i in c.execute("SELECT rowid, hostname FROM computers WHERE LOWER(hostname) = ?", (args[1],)):
                computers.append((i[0], i[1]));
            if len(computers) == 0:
                print "No such hostname."
                return
            elif len(computers) != 1:
                print "Hostname is ambigious."
                return
            computer = computers[0]
            for i in args[2:]:
                if (i.find('-') == -1):
                    try:
                        p = int(i)
                        c.execute("DELETE FROM ports WHERE computer_id = ? AND ports = ?", (computer[0], str(p)))
                        conn.commit()
                    except:
                        print "Invalid port specifier \"%s\"" % i
                else:
                    try:
                        start = int(i.split('-', 2)[0])
                        end = int(i.split('-', 2)[1])
                        c.execute("DELETE FROM ports WHERE computer_id = ? AND ports = ?", (computer[0], str(start) + "-" + str(end)))
                        conn.commit()
                    except:
                        print "Invalid port specifier \"%s\"" % i

# Help command.
class HelpCommand(Command):
    def handle(self, conn, c, args):
        print "reset - Clears and recreates the database."
        print "computer - Control computers."
        print "quota - Control quotas."
        print "tor - Configure transparent Tor."
        print "ports - Configure port blocking."
        print "help - This help."
        print "quit - Quits the control program."
