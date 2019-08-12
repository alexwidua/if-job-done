<img src="resources/readme_icon.png" align="right"/>

# if-job-done
> A if-keyshot-is-finished-rendering script

IFJD is a Python script that scrapes the current active Keyshot render window and triggers a webhook when the render is complete. This webhook can, as in this case, be connected
to a 3rd party app like IFTTT to send an email or push notification to your smartphone.

## Installation

Clone the repo wherever you'd like, then run `pip install --user --requirement requirements.txt` from the root directory.

#### Creating a IFTTT recipe
Assuming that you will be using IFTTT, you must first create a so-called IFTTT recipe to receive and utilise the webhook.
Medium write up soon.

## Usage

After the script has been started, it places itself in the taskbar <img src="resources/readme_tray.png" width="16"> and works in the background. When a rendering is started, it monitors the rendering and triggers a webhook when the rendering is finished or stopped (stopped manually or by a program crash).

A right click on the icon brings up a context menu (Open config or quit program). The icon tooltip gives vague information about the current status (`Idle, rendering image, rendering animation`).

## Configuration

Open the `config.ini` file make changes according to your wishes. Note that you must restart the script for the changes to take effect. 
- `update_interval` - Interval in seconds in which the script is looking for a suitable Keyshot handle.
- `finish_treshold` and `stop_treshold` - Treshold in seconds after which the webhook gets fired. These settings exist to prevent webhook spam when starting or stopping many short test renderings.
- `end_if_target_process_not_running` - End the script if Keyshot is not running. Useful if Keyshot and the script are started at the same time.
- `web_hook` - The actual webhook URL. The syntax for a usual IFTTT hook would be https://maker.ifttt.com/trigger/{eventName}/with/key/{key}
