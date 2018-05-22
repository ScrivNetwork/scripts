#!/usr/bin/python3
# Forked from https://raw.githubusercontent.com/wolfcryptogroup/xuma/master/xuma.py

import fcntl
import os
import socket
import struct
from subprocess import Popen, STDOUT, PIPE
import sys
import termios
import time

DEFAULT_COLOR = "\x1b[0m"
CYAN = "\033[0;36m"
BCYAN = "\033[1;36m"
YELLOW = "\033[93m"
MAX_LEN=struct.unpack('HHHH',fcntl.ioctl(0, termios.TIOCGWINSZ,struct.pack('HHHH', 0, 0, 0, 0)))[1]-5

def run(cmd_list):
	for cmd in cmd_list:
		proc=Popen(cmd,stderr=STDOUT,stdout=PIPE,shell=True)
		output=[]
		while True:
			line=proc.stdout.readline().strip().decode()[:MAX_LEN]
			if sys.argv[-1]!="-v":
				for i in range(len(output)):
					sys.stdout.write('\x1b[1A\r\x1b[2K')
				sys.stdout.flush()
			if not line: break
			output.append("\r  "+line)
			output=output[-5:]
			if sys.argv[-1]!="-v": print(DEFAULT_COLOR+"\n".join(output))
			else: print(DEFAULT_COLOR+output[-1])
			time.sleep(0.05)
		proc.wait()

if os.getuid()!=0:
	sys.exit("This program must be run with root privledges:\n\nsudo python3 {}".format(" ".join(sys.argv)))

os.system('clear')
print(BCYAN+"SCRIV Masternode Auto-Installer v.1.0 \n")
print(CYAN+"Updating & Upgrading Ubuntu...")

run(["apt-get update -y",
	'sudo DEBIAN_FRONTEND=noninteractive apt-get -y -o DPkg::options::="--force-confdef" -o DPkg::options::="--force-confold"  install grub-pc',
	"apt-get upgrade -y",
	"apt-get dist-upgrade -y"])

print(CYAN+"Creating Swap...")

run(["dd if=/dev/zero of=swapfile bs=1M count=3000",
	 "mkswap swapfile",
	 "swapon swapfile"])
with open('/etc/fstab','r+') as f:
	line="/swapfile none swap sw 0 0 \n"
	lines = f.readlines()
	if lines[-1]!=line:
		f.write(line)

print(CYAN+"Securing Server...")
run(["apt-get --assume-yes install ufw",
	 "ufw disable",
	 "ufw default allow outgoing",
	 "ufw default deny incoming",
	 "ufw allow openssh",
	 "ufw allow ssh/tcp",
	 "ufw limit ssh/tcp",
	 "ufw allow 7998/tcp",
	 "ufw allow 7979/tcp",
	 "ufw logging on",
	 "ufw --force enable",
	 "sudo apt-get install fail2ban -y",
	 "sudo service fail2ban start"])

print(CYAN+"Installing Build Dependencies...")
run(["apt-get install nano htop git -y",
	 "apt-get install build-essential libtool automake autoconf autogen libevent-dev pkg-config -y",
	 "apt-get install autotools-dev autoconf pkg-config libssl-dev -y",
	 "apt-get install libssl-dev libevent-dev bsdmainutils software-properties-common -y",
	 "apt-get install libgmp3-dev libevent-dev bsdmainutils libboost-all-dev -y",
	 "add-apt-repository ppa:bitcoin/bitcoin -y",
	 "apt-get update",
	 "apt-get install libdb4.8-dev libdb4.8++-dev -y",
	 "apt-get install libminiupnpc-dev -y"])


if os.path.exists('/scriv'): print(CYAN+"SCRIV is already installed!")
else:
	print(CYAN+"Downloading & Compiling SCRIV Wallet...")
	run(["git clone https://github.com/ScrivNetwork/scriv.git",
		 "cd scriv && chmod 755 autogen.sh",
		 "cd scriv && ./autogen.sh",
		 "cd scriv && ./configure",
		 "cd scriv && chmod 755 share/genbuild.sh",
		 "cd scriv && make"])
		 
print(CYAN+"Running SCRIV Wallet...")
run(['su - root -c "scriv/src/scrivd -daemon &> /dev/null" '])

print(YELLOW+"Open your desktop wallet console (Help => Debug window => Console) and generate your masternode outputs by entering: masternode outputs")
txid=input(DEFAULT_COLOR+"  Transaction ID: ")
tx_index=input("  Transaction Index: ")

print(YELLOW+"Open your desktop wallet console (Help => Debug window => Console) and create a new masternode private key by entering: masternode genkey")
priv_key=input(DEFAULT_COLOR+"  masternodeprivkey: ")

print(CYAN+"Saving config file...")
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
this_ip=s.getsockname()[0]
s.close()

run(["mkdir .scrivcore",
	 "cd .scrivcore"])

with open('.scrivcore/scriv.conf', 'w') as f:
	f.write("""listen=1
server=1
port=7979
externalip={0}:7979
masternode=1
masternodeaddr={0}:7979
masternodeprivkey={1}
addnode=185.243.112.228:7979
addnode=199.247.15.68:7979
addnode=45.32.135.51:7979
addnode=37.57.12.97:7979
addnode=45.32.237.234:7979
addnode=80.211.41.63:7979
""".format(this_ip, priv_key))

print(CYAN+"Restarting SCRIV Wallet...")
run(["cd",
	 "scriv/src/scriv-cli stop",
	 "sleep 30",
	 'su - root -c "scriv/src/scrivd -daemon &> /dev/null" ',
	 "watch scriv/src/scriv-cli getinfo"])