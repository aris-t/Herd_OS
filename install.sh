sudo apt update
sudo apt install python3-pip
sudo apt-get install git

sudo apt install libcap-dev
sudo apt install libgirepository1.0-dev libcairo2-dev cmake
sudo apt install gir1.2-gst-rtsp-server-1.0
sudo apt install nodejs npm -y

sudo apt install gir1.2-gst-plugins-bad-1.0

sudo apt install gstreamer1.0-nice



git clone git@github.com:aris-t/Herd_OS.git
# git remote set-url origin git@github.com:aris-t/Herd_OS.git

git clone https://github.com/suptronics/x120x.git
	# sudo i2cdetect -y 1

sudo apt install python3-gi gir1.2-gst-plugins-base-1.0 \
                gir1.2-gstreamer-1.0 gstreamer1.0-plugins-good \
                gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
                gstreamer1.0-libav gstreamer1.0-tools
pip install aiohttp websockets
pip install websockets


sudo apt install \
  gstreamer1.0-tools \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly \
  gstreamer1.0-libav

sudo apt install python3-gi gir1.2-gst-plugins-base-1.0 gir1.2-gstreamer-1.0

sudo apt install libcairo2-dev libgirepository1.0-dev pkg-config python3-dev

sudo apt install gstreamer1.0-libcamera

rm -r myenv
python -m venv myenv
source myenv/bin/activate
sed -i 's/include-system-site-packages = .*/include-system-site-packages = true/' myenv/pyvenv.cfg

pip install picamera2
pip install -r requirements.txt

cd frontend
npm install
npm run build
cd ..

sudo timedatectl set-ntp true
sudo pip install eclipse-zenoh --break-system-packages

sudo ln -s /home/sheepdog/Herd_OS/services/IFF.service /etc/systemd/system/IFF.service
sudo ln -s /home/sheepdog/Herd_OS/services/battery_monitor.service /etc/systemd/system/battery_monitor.service
sudo systemctl daemon-reload

sudo systemctl start IFF.service
sudo systemctl start battery_monitor.service


# pip install pygobject
# pip install ply

# python3 -m pip install meson
# export PATH="$HOME/.local/bin:$PATH"

# git clone https://git.libcamera.org/libcamera/libcamera.git
# cd libcamera
# meson setup build
# sudo ninja -C build install


# sudo apt -y install python3-picamera2

# sudo apt install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-libav gstreamer1.0-plugins-ugly gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-gl gstreamer1.0-plugins-base-apps libcamera-dev gstreamer1.0-libcamera
