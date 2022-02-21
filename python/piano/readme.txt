0. sudo apt-get install python3-tk libportaudio2 libsndio-dev

1. connect bluetooth
sudo apt-get install bluetooth libbluetooth-dev
pip3 install -r ../requirements.txt



2. Play mp3
sudo apt install ffmpeg

3 ALSA
sudo apt-get install alsa-utils
sudo apt-get install alsamixer
speaker-test - to test sounf
aplay ~/vanya/python/piano/sound/slide_switch.wav
aplay -L to see devices


4.  Jack
4.1. sudo apt-get install qjackctl


4.4  connect to keyboard
read https://www.rncbc.org/drupal/node/7 to setup patchbay
   automatic reread  patchbay after start qjackctl


5. Zyaddsubfx
sudo apt install zynaddsubfx
zynaddsubfx -a 

