# Verhalenmachine (Story Machine)

---
Erwin:
TODO: Andere manier van Volumio aansturen
TODO: Check minor todo's across files
TODO: Check weird sound when recording (adapter?)
TODO: Check static sound when not playing with David (adapter?)
TODO: Update Volumio?? (Move to latest version)
TODO: Stresstest!!!
TODO: Make easier setup script (upload everything, (re)move recordings, set name for playlist, ...)
TODO: Complete README
TODO: Create documentation
TODO: Create requirements.txt
TODO: Make it possible to insert mic later (catch exception?)

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

### 1. Install Volumio

<https://volumio.org/get-started>

### 2. Setup Volumio

Plugin network cable and electricity and startup the device.
Connect to <http://volumio.local/>.

* Select Output Device
<http://volumio.local/plugin/audio_interface-alsa_controller>

* Change Player Name
<http://volumio.local/plugin/system_controller-system>

* Change Hotspot Name & Password
<http://volumio.local/plugin/system_controller-network>

### 3. Checkout this script

Do this <https://help.github.com/articles/generating-an-ssh-key/>

```
cd /home/volumio/
git clone git@github.com:erwinelling/verhalenmachine.git
```

To update:

```
cd /home/volumio/verhalenmachine
git pull
```

### 4. Install (Python) dependencies

First install pip

```
sudo apt-get install python-pip
```

Then install MPD2

```
sudo pip install python-mpd2
```

Install Soundcloud

```
sudo pip install soundcloud
```

Install GPIO stuff

```
sudo apt-get install rpi.gpio
```

Install Serial port stuff (also available through pip)

```
sudo apt-get install python-serial
```

Install python development headers
```
sudo apt-get install python-dev
```

Install psutil
```
pip install psutil
```

### Remot3.it

For remote SSH/ web access setup Remot3.it

<http://forum.weaved.com/t/how-to-get-started-with-remot3-it-for-pi/1029>

sudo apt-get install weavedconnectd

### Add FIFO MPD output
```
cd /volumio/app/plugins/music_service/mpd
cp mpd.conf.tmpl mpd.conf.tmpl.bak
nano mpd.conf.tmpl
```

Add:
```
audio_output {
  type    "fifo"
  name    "my_fifo"
  path    "/tmp/mpd.fifo"
  format  "44100:16:2"
}
```
Change something in Volumio settings

```
/etc/init.d/mpd restart
```

### Add services

As per <http://www.raspberrypi-spy.co.uk/2015/10/how-to-autorun-a-python-script-on-boot-using-systemd/> and Give it the right permissions and enable our unit file as service

```
sudo chmod 644 /home/volumio/verhalenmachine/verhalenmachine.service
sudo chmod 644 /home/volumio/verhalenmachine/vumeter.service
sudo systemctl enable /home/volumio/verhalenmachine/verhalenmachine.service
sudo systemctl enable /home/volumio/verhalenmachine/vumeter.service
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
```

Make sure to use crontab and not sudo, so the cronjob will run for user pi.

Add:

```
*/15 * * * * /usr/bin/python /home/volumio/verhalenmachine/cron_upload.py > /home/volumio/verhalenmachine/cron_upload.log
*/15 * * * * /usr/bin/python /home/volumio/verhalenmachine/cron_recordcheck.py > /home/volumio/verhalenmachine/cron_recordcheck.log
```

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

## Run player as a service

As per <http://www.raspberrypi-spy.co.uk/2015/10/how-to-autorun-a-python-script-on-boot-using-systemd/> and Give it the right permissions and enable our unit file as service

```
sudo chmod 644 /home/pi/stormy/machine.service
sudo systemctl enable /home/pi/stormy/machine.service
```

To control or check the service manually:

```
sudo systemctl start verhalenmachine
sudo systemctl stop verhalenmachine
sudo systemctl restart verhalenmachine
sudo systemctl status verhalenmachine
```

To check logs:

```
cat /var/log/mopidy/mopidy.log
```


### TODO: Change default password?


### Handig
python -m serial.tools.miniterm /dev/ttyUSB0 -b 57600
python -m serial.tools.list_ports
192.168.211.1
ps ax | grep arecord
sudo kill <pid>


http://verhalenmachine.local/DEV/


###
Turn off volume control in Volumio
https://volumio.github.io/docs/User_Manual/Volume_Control_and_audio_quality.html
We use our own hardware for it.
