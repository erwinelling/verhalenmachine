# Verhalenmachine (Story Machine)

---
Erwin:
TODO: Check minor todo's across files
TODO: Cronjobs

TODO: Stresstest buttons
TODO: Stresstest everything
TODO: Make it possible to insert mic later (catch exception?)

TODO: Create documentation for users
TODO: Make easier setup script (upload everything, (re)move recordings, set name for playlist, ...)

TODO: Refactor?


Aan David vragen:
Gek geluid tijdens opname
Gek statisch geluid altijd
Gekke piepjes door aansturing klikaanklikuit

---
Verhalenmachine (Story Machine) is a RaspberryPi based audio player/ recorder/ Soundcloud uploader.

The player part is implemented on top of Volumio. It controls Volumio via MPD and presumes a custom enclosure outfitted with:

* 2 buttons: For play & stop and next.
* a volume slider: For volume control :) (controlled via Davids work)
* a VU meter: For display of output volume (controlled via Davids work)
* ...

The recorder part is implemented ...:

* 1 button: For record & stop.
* a VU meter: For display of input volume (controlled via )
* ...

The Soundcloud uploader ...:

*
*


## Setup

### 1. Install Volumio on an SD card

<https://volumio.org/get-started>

### 2. Boot it and setup Volumio

Plugin network cable and electricity and startup the device.
Connect to <http://volumio.local/>.

* Change Player Name to Verhalenmachine
<http://volumio.local/plugin/system_controller-system>

* Set audio output to Audio Jack
<http://volumio.local/plugin/audio_interface-alsa_controller>


* Turn off volume control in Volumio
<http://volumio.local/plugin/system_controller-network>

We use our own hardware for it and it improves audio quality.
<https://volumio.github.io/docs/User_Manual/Volume_Control_and_audio_quality.html>

* Change Hotspot Name & Password
<http://volumio.local/plugin/system_controller-network>

* Enable SSH access

<https://volumio.github.io/docs/User_Manual/SSH.html>


### 3. Connect with SSH and checkout this script

```
ssh volumio@verhalenmachine.local
```

```
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```

```
cd /home/volumio/
git clone https://github.com/erwinelling/verhalenmachine.git
```

To update:

```
cd /home/volumio/verhalenmachine
git pull
```

### 4. Install (Python) dependencies

Install GPIO stuff

```
sudo apt-get install rpi.gpio
```

Install python development headers
```
sudo apt-get install python-dev
```

Install pip

```
sudo apt-get update && sudo apt-get install python-pip
```

Install Soundcloud, psutil, socketIO and MPD2

```
sudo pip install soundcloud psutil socketIO-client-2 python-mpd2
```

### Install Remot3.it

For remote SSH/ web access setup Remot3.it

<https://remot3it.zendesk.com/hc/en-us/articles/115006015367-Installing-the-remot3-it-weavedconnectd-daemon-on-your-Raspberry-Pi>

```
sudo apt-get install weavedconnectd
sudo weavedinstaller
```

### Add services

As per <http://www.raspberrypi-spy.co.uk/2015/10/how-to-autorun-a-python-script-on-boot-using-systemd/> and Give it the right permissions and enable our unit file as service

```
sudo chmod 644 /home/volumio/verhalenmachine/verhalenmachine.service
sudo systemctl enable /home/volumio/verhalenmachine/verhalenmachine.service
```

To control or check the service manually:

```
sudo systemctl start verhalenmachine
sudo systemctl stop verhalenmachine
sudo systemctl restart verhalenmachine
sudo systemctl status verhalenmachine
```

### Add cronjobs

```
chmod a+x /home/volumio/verhalenmachine/cron_upload.py
chmod a+x /home/volumio/verhalenmachine/cron_recordcheck.py
crontab -e
sudo chown root: cron_*.log
```

Make sure to use crontab and not sudo, so the cronjob will run for user pi.

Add:

```
*/15 * * * * /usr/bin/python /home/volumio/verhalenmachine/cron_upload.py > /home/volumio/verhalenmachine/cron_upload.log
*/15 * * * * /usr/bin/python /home/volumio/verhalenmachine/cron_recordcheck.py > /home/volumio/verhalenmachine/cron_recordcheck.log
```
<!--
## Add logs for cron:

```
sudo nano /etc/rsyslog.conf
```

and uncomment the line

```
# cron.*                          /var/log/cron.log
```

After that, you need to restart rsyslog via

```
$ sudo /etc/init.d/rsyslog restart
```

## TODO: To check logs:

```
cat /var/log/syslog
``` -->

<!--
### Handig
python -m serial.tools.miniterm /dev/ttyUSB0 -b 57600
python -m serial.tools.list_ports
192.168.211.1
ps ax | grep arecord
sudo kill <pid> -->

###

# When connecting to new network

https://volumio.github.io/docs/User_Manual/Quick_Start_Guide

Turn it on

Wait for startup

Connect to Wifi Network Verhalenmachine with password verhalenmachine

Setup Wifi connection
http://192.168.211.1/plugin/system_controller-network

It should now be reachable at
http://verhalenmachine.local/


# Convenient for testing

cd tail -f ~/verhalenmachine/verhalenmachine.log
