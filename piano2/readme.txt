0. sudo apt-get install python3-tk

2. Play mp3
sudo apt install ffmpeg

3 ALSA
sudo apt-get install alsa-tools libasound2-dev
speaker-test - to test sound
aplay ~/proj/vanya/python/piano2/sound/slide_switch.wav
aplay -L  - to see devices


4. Zyaddsubfx
1. sudo apt install zynaddsubfx
2. test zynaddsubfx -a -I alsa -O alsa
3. use https://github.com/zynaddsubfx/zyn-fusion-build to build zynaddsubfx
git clone https://github.com/zynaddsubfx/zyn-fusion-build zyn-fusion-build
cd zyn-fusion-build
make -f Makefile.linux.mk all

4. apply patch  zynaddsubfx_vanya.patch
cd src/zynaddsubfx
git apply ~/proj/vanya/python/piano2/zynaddsubfx_vanya.patch

5. and rebuild
cd -
make -f Makefile.linux.mk all

./build/build-zynaddsubfx-linux-demo/src/zynaddsubfx


--not-fullscreen --zynaddsubfx-path /home/sokirko/proj/zyn-fusion-build/build/build-zynaddsubfx-linux-demo/src/zynaddsubfx