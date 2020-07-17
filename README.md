<img src="resources/readme_icon.png" align="right"/>

# if-job-done

`if-job-done` is a Python script that scrapes an active Keyshot instance and fires a webhook once the render state changes (finished or stopped). The webhook can be connected to e.g. [IFTTT](https://ifttt.com/) to send a push notification or email once the rendering is done.

Supports Keyshot `>= 6`.

## Motivation

In larger computer labs there is the problem that render workstations often remain occupied for an unnecessarily long time, even though the render job is already finished. This is due to the fact that students do not have any remote information about the status of their renderings and therefore only sporadically check the workstation every few hours. This script is a robust solution to inform (e.g.) students about a finished rendering or when a render job stopped unexpectedly. With this script the usage and 'downtime' of each workstations can be optimized. The script was succesfully used in a medium sized lab (university, 30-40 workstations).

## Installation

Clone the repo and run `pip install --user --requirement requirements.txt` from the root directory.

#### Creating a IFTTT recipe

Assuming that you will be using IFTTT, you must first create a IFTTT recipe to get the webhook endpoint and connect it to a action Read the [IFTTT docs](https://platform.ifttt.com/docs) for more.

## Usage

After the script has been started, it minimizes itself to the taskbar <img src="resources/readme_tray.png" width="16"> and runs in the background. The script must be stopped manually or the value `end_if_target_process_not_running` must be set to `true` in the [config](./cfg/config.ini) file.

Right click the taskbar icon to open the config file, exit the script or get status information about the current render (`Idle, rendering image, rendering animation`).

## Configuration

Open the `config.ini` file to config the script. :warning: Note that the changes only become effective after the script is restarted.

-   `update_interval` - Interval in seconds in which the script is looking for a suitable Keyshot handle.
-   `finish_treshold` and `stop_treshold` - Treshold in seconds after which the webhook gets fired. These settings exist to prevent webhook spam when starting or stopping many short test renderings.
-   `end_if_target_process_not_running` - End the script if Keyshot is not running. Useful if Keyshot and the script are started at the same time.
-   `web_hook` - The actual webhook URL. E.g. https://maker.ifttt.com/trigger/{eventName}/with/key/{key}
