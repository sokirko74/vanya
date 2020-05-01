1. connect bluetooth
sudo apt-get install bluetooth libbluetooth-dev
pip3 install pybluez

2. Play mp3
sudo apt install ffmpeg

3 ALSA
sudo apt-get install alsa-utils
sudo apt-get install alsamixer
speaket-test - to test sounf
aplay ~/vanya/piano/sound/slide_switch.wav
aplay -L to see devices


4.  Jack
4.1. sudo apt-get install jackd2 qjackctl pulseaudio-module-jack

4.2. play pulseaudio through jack
https://askubuntu.com/questions/572120/how-to-use-jack-and-pulseaudio-alsa-at-the-same-time-on-the-same-audio-device

4.2.1 RESTART!! 

4.3. test jack sound 
jack_simple_client

4.4  connect to keyboard
read https://www.rncbc.org/drupal/node/7 to setup patchbay
   automatic reread  patchbay after start qjackctl


5. Zyaddsubfx
sudo apt install zyaddsubfx
zynaddsubfx -a 

