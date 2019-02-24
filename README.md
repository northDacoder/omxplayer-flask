# omxplayer queue player

Create Web pages to play successive videos thru ` omxplayer ` onto RaspberryPi.

## hardware

- raspberry pi

## init

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `secret.py` file to overwrite config variables.


## launch

Execute commands into ` screen `.

```
export FLASK_APP=player.py
# if you want to debug and auto refresh
export FLASK_DEBUG=1
# your web server will be reachable from anywhere
python -m flask run --host=0.0.0.0

# other screen
python daemon.py
```
