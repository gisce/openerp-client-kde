# Installation

Requirements

``` bash
sudo apt-get install python3 python3-pyqt5 python3-dbus.mainloop.pyqt5 python3-pyqt5.qtwebkit python3-pyqt5.qtsvg
```

Create virtual env
``` bash
mkvirtualenv erpkoo -p /usr/bin/python3 --system-site-packages
```

Install python requirements
``` bash
pip install pyserial erppeek raven<5.0
```