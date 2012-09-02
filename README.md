QuotaTracker
============

Tracks and throttles internet usage using IPTables and Traffic Control.  Licensed under MIT.

Installation
-----------------
You should install QuotaTracker into `/srv/filter`.  There are provided systemd scripts
to easily get it set up.  Just copy them across and enable them to have the filtering
system run at start up.  *Do not start the daemon until you initialize the database.*

You can install into an alternate directory, but you will need to update both the systemd
scripts and the Python scripts (they automatically chdir to `/srv/filter` so they can be
called from anywhere).

For convenience, you might also want to create some symbolic links:
```shell
ln -s /srv/filter/usage /sbin/qtusage
ln -s /srv/filter/control /sbin/qtcontrol
```

Finally, you must run the `reset` command in the control program before starting the
daemon.  This will create / reset the database so that other parts of QuotaTracker
work correctly.

Getting Started
------------------
Before the system will permit any traffic, you need to define the computers that exist on
the network.  The daemon will automatically resolve hostnames to IP address when modifying
iptables, so you should provide hostnames (as they are less likely to change).  If the box
does not have the same domain set as other computers, use the fully-qualified host name of
each computer.

**qtcontrol Examples:**
```
> computer add james-pc James
Added computer james-pc (James).
Assigned computer james-pc a quota of 0 bytes over 0 seconds.
> computer list
7 computers configured.
 - james-pc (James)
 - storm (Nathan)
 - leigh-pc (Leigh)
 - peter-pc (Peter)
 - nathan-laptop (Nathan)
 - nathan-pc (Nathan)
 - nathans-ipod (Nathan)
> quota set 3600 52428800 # Permit computers to use 50MB in 1 hour.
Assigned all computers a quota of 52428800 bytes over 3600 seconds.
```

qtusage shows the status of every computer, and indicates whether they are being throttled
with the `(\*)` indicator.  It is best used with the `watch` command, like so:
```
watch qtusage
```

If you are not experiencing any throttling, ensure that the `tcconfig` file is set to the
correct interface (this file also allows you to tweak the throttling speed).

Transparent Tor
------------------
QuotaTracker can also enable Tor on a per computer basis.  Ensure you have Tor enabled on
the box that QuotaTracker is installed on, following the instructions at these URLs:

https://gitweb.torproject.org/tor.git?a=blob_plain;hb=HEAD;f=doc/tor-rpm-creation.txt
https://trac.torproject.org/projects/tor/wiki/doc/TransparentProxy#AnonymizingMiddlebox

Now when you want, you can enable or disable Tor on a per-computer basis using `qtcontrol`:
```
Quota management system - control program
> tor list
1 computers using Tor:
 - james-pc (James)
6 computers not using Tor:
 - storm (Nathan)
 - leigh-pc (Leigh)
 - peter-pc (Peter)
 - nathan-laptop (Nathan)
 - nathan-pc (Nathan)
 - nathans-ipod (Nathan)
> tor on james-pc
Enabled transparent Tor for james-pc.
Verify by accessing https://check.torproject.org/ from the machine.
It might take a minute for the changes to apply.
> tor off james-pc
Disabled transparent Tor for james-pc.
It might take a minute for the changes to apply.
```
