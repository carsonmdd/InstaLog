# Instalog
Instalog is an intuitive and user-friendly offline data-logging app designed to efficiently capture and manage real-time data primarily for aerial surveys of marine birds and mammals.

## Features
- Real-time data logging from serial GPS devices
- Customizable species shortcuts allow for fast and efficient entry
- Generates CSVs and Shapefiles for observations and recorded track
- Easily continue projects by loading an observation CSV
- Simple and clean user interface
- Windows and macOS support

## Notes
- Pyinstaller was used to bundle the app into a single executable for end users
- See InstaLog's executables, user guide, and settings file here: (https://drive.google.com/drive/folders/11lNMJhH1kuCFg-K_dro7AFz68LBna3g-?usp=sharing)

## Installation
1. Clone the repo
- Clone the "main" branch for macOS:
    ```bash
    git clone https://github.com/carsonmdd/InstaLog.git
    ```
- Clone the "windows" branch for Windows:
    ```bash
    git clone -b windows https://github.com/carsonmdd/InstaLog.git
    ```
2. Navigate to project directory
    ```bash
    cd InstaLog
    ```
3. (Optional) Use a virtual environment to avoid installing dependencies globally.
- Create a virtual environment:
    ```bash
    python -m venv .venv
    ```
- Activate the virutal environment:
    - macOS:
        ```bash
        source .venv/bin/activate
        ```
    - Windows:
        ```bash
        .venv/Scripts/activate
        ```
4. Install the required dependencies
    ```bash
    pip install -r requirements.txt
    ```

## Usage
### Running the app
#### Settings
- InstaLog's settings can be configured in the settings.json file
- There are two settings in this file:
    - baud_rate: baud rate for the app to use with the GPS
    - shortcuts: a list of key-value pairs that represent species shortcuts

#### Windows
1. Install USB-to-Serial Driver
    - If you are using a UBS-to-serial cable, you may need to install a driver for it to work properly. You can download the driver from the manufacturer's website (e.g., [CP210x USB to UART Bridge VCP Drivers](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers?tab=downloads) for Silicon Labs chips).
2. Turn on your serial GPS device.
3. In the settings.json file, ensure the baud_rate setting matches your GPS's baud rate.
4. Connect the GPS to your computer via USB.
5. Run the app:
    ```bash
    python main.py
    ```

#### macOS:
1. Turn on your serial GPS device.
2. In the settings.json file, ensure the baud_rate setting matches your GPS's baud rate.
3. Connect the GPS to your computer via USB.
4. Run the app:
    ```bash
    python main.py
    ```

### Navigating the GUI
- Create a new observations (obs) CSV with the "**New CSV**" button
- Load an existing obs CSV with the "**Load CSV**" button
- Delete the last row of the table with the "**Delete last row**" button
- Revert the most recent add/delete row action with the "**Undo**" button
- Log data by entering data in the Entry Viewer following the general format of a species name (or shortcut) followed by the count observed
- The "**Error Log**" displays an error when coordinates cannot be read from the GPS
- Data can be directly edited in the table as well

### Output
Instalog outputs an observations CSV, track CSV, observations shapefile, and a track shapefile. Observations are for the user-recorded data entered into the app. The track is created by a background thread continuously reading coordinates from the GPS every 2-3 seconds.