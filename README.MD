# Verhalenmachine (Story Machine)

Verhalenmachine (Story Machine) is a RaspberryPi based audio player/ recorder/ Soundcloud uploader.

The player part is implemented on top of Volumio. It controls Volumio via MPD and presumes a custom enclosure outfitted with:

* 2 buttons: For play & stop and next.
* a volume slider: For volume control :)
* a VU meter: For display of output volume.
* ...

The recorder part is implemented ...:

* 1 button: For record & stop.
* VU meter: For display of input volume.
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
cd /home/pi/
git clone git@github.com:erwinelling/stormy.git
```

To update:

```
cd /home/pi/stormy
git pull
```

### 4. Install (Python) dependencies

First install pip

```
sudo apt-get install python-pip
```

Then install MPD

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


### Remot3.it

For remote SSH/ web access setup Remot3.it

<http://forum.weaved.com/t/how-to-get-started-with-remot3-it-for-pi/1029>

sudo apt-get install weavedconnectd


### Change default password?

### Do something with Dyndns

## Elements
## Dependencies

python-mpd2
soundcloud