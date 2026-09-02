# AccessiGaming Cam

A Computer Vision desktop software designed to empower disabled gamers to play shooters and other PC games using just a webcam. It tracks head movements and facial gestures to simulate smooth mouse and keyboard inputs via DirectX-compatible `pydirectinput`.

## Features
- **Head Tracking for Aiming**: Pitch (up/down) and Yaw (left/right) head movements map to relative mouse movements (joystick-like velocity control).
- **Left Eye Blink**: Simulates a **Left Click** (Shoot). Can be held down for automatic weapons.
- **Right Eye Blink**: Simulates a **Right Click** (Aim/ADS). Can be held down.
- **Mouth Opening**: Simulates pressing the **Space** key (Jump) by default. (Can be easily configured to 'r' for reload or any other key).
- **Always-on-top Overlay**: A transparent-like floating window showing your camera feed, face mesh, and live metrics to help you easily calibrate and monitor inputs.

## Installation

1. Ensure you have Python 3.8 or newer installed on your Windows machine.
2. Install the required dependencies using pip:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: This script relies on `pydirectinput` which leverages Windows DirectX inputs, so it is strictly intended for Windows environments.*

## Usage & Calibration

1. Run the application:
   ```bash
   python main.py
   ```
2. A floating window will appear on top of other windows. Position yourself comfortably so your face is clearly visible and well-lit.
3. **Calibrate Center**: Look straight at your screen (your natural resting position) and press the **'C'** key on your keyboard. This sets your "zero" point for aiming.
4. **Aiming Control**: 
   - Tilt your head **Left/Right** to move the mouse horizontally.
   - Tilt your head **Up/Down** to move the mouse vertically.
   - The further you tilt your head past the designated deadzone, the faster the crosshair moves (similar to tilting a console controller joystick).
5. **Exit**: Press the **'Q'** key while the OpenCV window is focused to cleanly exit the application and release any held keys.

## Configuration
Open `main.py` in any text editor to customize the script to your specific needs. Look for the `--- CONFIGURATION ---` block at the top:
- `SENSITIVITY_X` & `SENSITIVITY_Y`: Increase for faster aiming, decrease for more precise control.
- `DEADZONE_PITCH` & `DEADZONE_YAW`: Adjust the area where head movement is ignored to prevent accidental micro-jitters.
- `INVERT_X` & `INVERT_Y`: Set these to `True` if your mouse moves in the opposite direction of what you expect.
- `KEY_MOUTH`: Change `'space'` to `'r'` or any other key string if you prefer mouth opening to trigger a different action.
- `BLINK_THRESHOLD` & `MOUTH_THRESHOLD`: Adjust if the camera is not detecting your blinks or mouth openings reliably. Lower EAR values require tighter eye closures; higher MAR values require wider mouth openings.

## Troubleshooting
- **Input not registering in game?** Run the Command Prompt or terminal as **Administrator** before executing the script. Some anti-cheat systems and games require administrative privileges for virtual inputs to be injected successfully.
- **Camera is lagging or tracking is poor?** Ensure your room is well-lit. Webcam exposure auto-adjustments in low light can drastically lower your camera's frame rate and introduce latency.
