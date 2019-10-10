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

* Just assume LGR will always get same DHCP address, 10.42.0.174
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

Install Grafana for local data visualization. 
```
sudo apt install grafana -y
```

Do initial setup
* Package automatically creates and starts system service, `grafana-server`.
* Login to <http://localhost:3000/> with default user (admin/admin)
* --> setup InfluxDB with test database
* Add influxdb as data source and test... OK!



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
	  `CREATE USER lar WITH PASSWORD 'losgatosn2oco' WITH ALL PRIVILEGES`
	* (that's enough, exit for now)
* Modify `/etc/influxdb/influxdb.conf` to enable auth, then restart service:
  ```diff
  -  auth-enabled = false
  +  auth-enabled = true
  ```
* Now continue with grafana setup...
* Now feed data in with Python3:
  ```
  pip3 install influxdb
  ```



## Telegraf




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


* use NUT-Monitor and admin user creds to modify UPS variables: `upsrw <upsname>`
	* battery.charge.low = 40 (%)
	* battery.runtime.low = 600 (sec)


* the Back-UPS model will drain out battery instead of killing power 
  [ref](https://forums.apc.com/spaces/4/back-ups-surge-protectors/forums/general/88936/how-to-automatically-shutdown-ups-after-server-shutdown)
	* because extra cmds prob reqd, restrict this config to specific APC unit:
	  use `lsusb` to identify vendor/product ids, then add to `ups.conf`:

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






