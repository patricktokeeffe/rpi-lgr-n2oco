# LGR N2O/CO Gateway Setup Notes


## O/S Setup

todo


Other software utilities installed:
* tmux (need to setup session reconnector)
* git
* glances


-> use uninstall line from RV-server, plus remove:
* transmission-gtk


### force HDMI on

```
sudo nano /boot/config.txt
```
```diff
-#hdmi_force_hotplug=1
+hdmi_force_hotplug=1
```
```diff
-#hdmi_drive=2
+hdmi_drive=2
```


### fix chromium keyring unlock issue

* create new launcher in ~/.local/applications with extra CLI opts

```
cp /usr/share/applications/chromium-browser.desktop ~/.local/share/applications/
sed -i 's/Exec=chromium-browser/& -password-store=basic/g' ~/.local/share/applications/chromium-browser.desktop
```


## VNC server setup

* Download both server & viewer .deb packages from RealVNC website
* Double-click to install
* Viewer readily available from start menu
* Server must be enabled manually with systemd

Afterwards, get panel icon for service that expands into information
window. Users see the wifi address! Works great from office - even
get passphrase confirmation prompt so using advanced auth. 

Viewer also working great with LGR. Stayed connected overnight no prob.

Server config todo:
* Under privacy, disable option that disconnects idle users
* Under connections, disable 'show accept/reject prompt for each connection' 


# Remote Desktop Protocol setup

Do *not* install `xrdp`:
* Conflicts with RealVNC Server
* Does not attach to local session anyway



## Internet connection sharing 

On RPi, connected to internet via wired [ref](https://askubuntu.com/questions/359856/share-wireless-internet-connection-through-ethernet):

1. Connect RPi to wireless network
#. Replace wired network connection with crossover to LGR
#. Test internet still accessible.
#. Open network icon > "Edit connections..."
#. Double-click on 'Wired connection 1' (LAN)
#. On IPv4 Settings tab, change method from 'Automatic (DHCP)' to
   'Shared to other computers'
#. Save

On LGR:

1. Verify using DHCP network config, not static IP
2. Verify connected to RPi via crossover cable (not tested std)
3. Check LGR receives DHCP address from RPi (`/sbin/ifconfig`)
4. If no wired interface present, use `/sbin/ifup eth0` to enable then retry.

Still working great next day. Should now test reboots, connecting to
different wifi, etc.


## Software updates

Use 'Software & Update' control panel application:
* Updates: never notify for new Ubuntu versions (to ignore 18.04 notices)
* Verify security updates are download and install automatically


## Screensaver config

* Do not lock screen when enabling screensaver


## Disable annoying keyring prompt

See new file `~/.config/chromium-flags.conf` - seemed to work!

Should follow up here: 
* https://askubuntu.com/questions/867/how-can-i-stop-being-prompted-to-unlock-the-default-keyring-on-boot
* https://support.google.com/chrome/thread/3452787?hl=en


## Linking to LGR unit

* give LGR static IP address, 10.42.0.10 -> also specify gateway
* On LGR, temporarily ENable ssh password login
* On RPi:
	* Generate local ssh creds (`ssh-keygen`)
	* Run `ssh-copy-id lgr@10.42.0.174` to authorize RPi permanently
* On LGR, re-DISable ssh password logins

Now try:
* Nemo file editor > Connect to server... > SSH: lgr @ 10.42.0.174
* Open directly into data folder `/home/lgr/data`
	* maybe change so can reach screenshots?
* Create bookmark entry 'LGR Data'


-> Install samba to browse to data via network share
`sudo apt install samba`
...ok, LGR only shows $print share, not data


## Logging LGR serial data

* Enable user 'lar' to use serial port: `sudo addgroup lar dialout`
* Logout/in to make effective




## NTP setup

Edit `/etc/ntp.conf` on LGR analyzer:
* add RPi to trusted client network (i.e. 10.42.0.0 mask 255.255.255.0)
* add RPi as potential sync client? probably bad idea since it lacks an RTC
* possibly enable `tinker panic 0` param to enable very large step change at boot

Now from RPi, query for status directly:
````
ntpq -pn 10.42.0.174
````


## Grafana

[Install](https://grafana.com/docs/installation/debian/) Grafana for local data
visualization. Add the Grafan repo to get the latest version with alerting:
```
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt update
sudo apt install grafana -y
```

Enable & start the system service:
```
sudo systemctl enable grafana-server
```

Do initial setup
* Package automatically creates and starts system service, `grafana-server`.
* Login to <http://localhost:3000/> with default user (admin/admin)
* --> setup InfluxDB with test database
* Add influxdb as data source and test... OK!
* update admin username/email to lab generic



## Influxdb

Install influxdb for storing timeseries data. (why isn't client included?)
```
sudo apt install influxdb influxdb-client
```

Do setup:
* Package automatically creates and starts system service, `influxd`.
* Launch command line shell: `influx` (reqs installing `influxdb-client`)
	* create new DB: `CREATE DATABASE lgrtest1`
	* create admin user (reqd to enable auth, which is reqd for grafana): 
	  `CREATE USER lgr WITH PASSWORD 'losgatosn2oco' WITH ALL PRIVILEGES`
* Modify `/etc/influxdb/influxdb.conf` to enable auth, then restart service:
  ```diff
  -  auth-enabled = false
  +  auth-enabled = true
  ```
* Now continue with grafana setup...
* No, do not use `pip` or `pip3` because they will fuck up your Python package
  permissions. instead, install package using apt
  ```
  sudo apt install python3-influxdb
  ```
* apt gives very old version. now use *pip3* to upgrade to 5.x:
  ```
  sudo -H pip3 install --upgrade influxdb
  ```

Optimizing influxdb resource usage:
* inside `/etc/influxdb/influxdb.conf`:
    * ~~disable metaservice/raft group participation~~
        * this will break influxdb, possibly permanently (e.g. data reset possibly fixes)
    * ~~change `query-log-enabled` to `false`~~
* update to latest version instead: https://docs.influxdata.com/influxdb/v1.7/introduction/installation/
```
wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add -
source /etc/lsb-release
echo "deb https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
sudo apt update
```

before installing, backup existing data and conf then purge old packages
```
sudo cp -r /var/lib/influxdb /var/backups/influxdb-0.10.0-1
sudo cp /etc/influxdb/influxdb.conf /var/backups/influxdb-0.10.0-1.conf
sudo apt remove influxdb influxdb-client
sudo apt autoclean
```

OK now finally install, then ignore any dpkg errors (because should not be any),
and enable at boot by unmasking:
```
sudo apt install influxdb
sudo systemctl unmask influxdb.service
```

OK! now recreate users and database expected by DAQ script...

Optimize influx for low resource usage:
* disable logging for metaservice (meta section)
* disable query logging (in data section)
* disable internal monitoring service (monitor -> store-enabled=false)
* disable request logging (http section)
* suppress write request logging (http section)
* increase log level from info->warn (logging section)





## Launchers

Create some useful launcher shortcuts:
* Open LGR command line
* Halt LGR analyzer
* Reboot LGR analyzer
* Monitor LGR clock (NTP) status

N.B. ([ref](https://github.com/mate-desktop/mate-panel/issues/57)): to get the
nice looking `mate-terminal` instead of classic xterm, use this command format
in launchers (and do not choose application in terminal): `mate-terminal -e '<cmd>'`



## UPS & LGR

* Buy APC-specific usb cable to connecting to Back-UPS XS 1500 unit
* install supporting software:
  ```
  sudo apt install nut nut-monitor
  ```
* modify `/etc/nut/nut.conf` to be "standalone" mode
* modify `/etc/nut/ups.conf` with new section:
```
[bx1500g]
	driver = usbhid-ups
	port = auto
	desc = "APC Back-UPS XS 1500"
```
* restart both `nut-server` and `nut-client` services...
* do not bother copying `/lib/udev/rules.d/52-nut-usbups.rules` to `/etc/udev/rules.d/`
	* XXXX MIGHT WANT TO REVISIT
* create users: `sudo nano /etc/nut/upsd.users`
```diff
+[admin]
+    password = yourgreatpassword
+    allowfrom = localhost
+    actions = SET
+    instcmds = ALL
+
+[upsmon]
+	 password = somelongpassphrase
+    allowfrom = localhost
+    upsmon master
```
* specify actions for monitoring daemon to take: `sudo nano /etc/nut/upsmon.conf`
```diff
 # MONITOR myups@localhost 1 upsmon pass master  (or slave)
+MONITOR bx1500g@localhost 1 upsmon somelongpassphrase master
```
	* TODO: modify shutdown command
	* maybe: increase the `FINALDELAY` param


* ~~use NUT-Monitor and admin user creds to modify UPS variables: `upsrw <upsname>`~~
    * UPS does not retain settings changes after power loss..
* since UPS lacks advanced power reset features and LGR doesn't have ACPI,
  defaults are prob best so UPS is essentially drained before shutdown occurs


* the Back-UPS model will drain out battery instead of killing power
  [ref](https://forums.apc.com/spaces/4/back-ups-surge-protectors/forums/general/88936/how-to-automatically-shutdown-ups-after-server-shutdown)
	* because extra cmds prob reqd, restrict this config to specific APC unit:
	  use `lsusb` to identify vendor/product ids, then add to `ups.conf`:

* APC says PowerChute Personal edition applies to Back-UPS, and that after 1 or 2
  minutes the UPS will shut itself off after hibernating computers

```
vendorid = "051d"
productid = "0002"
```


* possible commands for shutdown `upscmd <upsname>`
	* load.off.delay (turn off load after delay)
	* shutdown.reboot (shut down load briefly while rebooting ups)



questions to answer:
* does load.off.delay also turn off ups?
* does restoring power with load off restore loads?


required configuration for LGR analyzer:
* must have static IP address, for reliable ssh command sending
* create separate ssh key for root login (-> `/var/lib/nut/.ssh/id_rsa`)
```
sudo -u nut ssh-keygen
```
* must have root ssh login enabled (so can send `shutdown -h` command)
    * so temporarily enable password login
    * and also permanently enable root ssh login
    * configure nut service for root login
```
sudo ssh-copy-id -i /var/lib/nut/.ssh/id_rsa root@10.42.0.10
```
    * then re-disable passwords login
* ...can take up to 15 entire seconds to flush to disk and display safe shutdown OK
    * so bump FINAL_DELAY 5 -> 20 seconds
    * and trigger shutdown LGR command at any of FSD,  SHUTDOWN, LOWBATT flags





## Watchdog

> Should do this sooner, since InfluxDB+Chromium tends to crash the machine
> (because chrome sucks at memory management)

```
sudo nano /boot/config.txt
```
```diff
-#dtparam=watchdog=off
+dtparam=watchdog=on
```
```
sudo reboot
```

```
sudo apt install watchdog -y
sudo bash -c "cp /lib/systemd/system/watchdog.service /etc/systemd/system/ > echo 'WantedBy=multi-user.target' >> /etc/systemd/system/watchdog.service"
sudo reboot

```
sudo nano /etc/watchdog.conf
```
* enable (uncommment) some tests
* fix/specify watchdog-timeout value (https://www.raspberrypi.org/forums/viewtopic.php?t=147501)


## fail2ban

To prevent log flooding, which causes unecessary SD card writes, install `fail2ban`:
```
sudo apt install fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local
```

* add IP exclusions, if desired
* enable ssh jail: `enabled = true` under `[sshd]`
    * add `filter = sshd` statement as well

Restart service.










