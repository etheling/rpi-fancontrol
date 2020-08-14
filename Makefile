all : install

install:
	sudo apt -y install python3-pip
	sudo pip3 install -r ./src/requirements.txt
	sudo cp -f ./src/fancontrol.py /usr/local/sbin
	-sudo systemctl stop fancontrol
	-sudo systemctl disable fancontrol
	sudo cp -f ./systemd/fancontrol.service /lib/systemd/system
	sudo cp -f ./src/fancontrol.conf /etc
	sudo systemctl enable fancontrol
	sudo systemctl start fancontrol
	sudo systemctl status fancontrol

uninstall:
	-sudo systemctl stop fancontrol
	-sudo systemctl disable fancontrol
	sudo rm -vf /lib/systemd/system/fancontrol.service
	sudo rm -vf /etc/fancontrol.conf
