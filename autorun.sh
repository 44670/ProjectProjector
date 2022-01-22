#!/bin/ash
cd /opt/shell

# Load kernel modules
kernel_ver=$(uname -r)
ko_path="/lib/modules/$kernel_ver"
killall udhcpc wpa_supplicant lircd lircd-uinput bluealsa
modprobe brcmfmac
modprobe uinput
modprobe snd_bcm2835
modprobe bcm2835_codec 
modprobe bcm2835_v4l2 
modprobe pwm_bcm2835
modprobe gpio_ir_recv  
modprobe raspberrypi_hwmon   
modprobe hci_uart       
./btuart.sh

mkdir /var/run/lirc
lircd
lircd-uinput -a &

wpa_supplicant -Dnl80211 -iwlan0 -c/etc/wpa_supplicant.conf &
sleep 1
udhcpc -i wlan0 &

export LIBASOUND_THREAD_SAFE=0
bluealsa -p a2dp-source &

while : 
do
	rm /run/next
	touch /run/next
	echo "Starting shell..."
	python3 main.py
	source /run/next
	sleep 5
done

