import cv2
import mediapipe as mp
import pydirectinput
import numpy as np
import math
import keyboard
import time
# --- CONFIGURATION ---
# Aiming Sensitivity
SENSITIVITY_X = 3.0
SENSITIVITY_Y = 3.0
DEADZONE_PITCH = 3.0  # Degrees of head tilt to ignore (up/down)
DEADZONE_YAW = 3.0    # Degrees of head tilt to ignore (left/right)

# Blink & Mouth Thresholds
BLINK_THRESHOLD = 0.20   # Eye Aspect Ratio threshold for blinking
MOUTH_THRESHOLD = 0.35   # Mouth Aspect Ratio threshold for opening mouth

# Keybindings
KEY_MOUTH = 'space'      # Can be 'space', 'r', etc.

# Invert Axes if needed (True/False)
INVERT_X = False
INVERT_Y = False
# ---------------------

# PyDirectInput settings
pydirectinput.PAUSE = 0  # Remove delay for faster input
pydirectinput.FAILSAFE = False  # Prevent accidental crashing if mouse goes to corner

mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def get_landmark_point(landmark, w, h):
    return (int(landmark.x * w), int(landmark.y * h))

def get_ear(landmarks, corners, top, bottom, w, h):
    """Calculates the Eye Aspect Ratio (EAR) for blink detection."""
    c1 = get_landmark_point(landmarks[corners[0]], w, h)
    c2 = get_landmark_point(landmarks[corners[1]], w, h)
    t1 = get_landmark_point(landmarks[top[0]], w, h)
    b1 = get_landmark_point(landmarks[bottom[0]], w, h)
    t2 = get_landmark_point(landmarks[top[1]], w, h)
    b2 = get_landmark_point(landmarks[bottom[1]], w, h)
    
    hor_dist = distance(c1, c2)
    if hor_dist == 0:
        return 0
    ver_dist1 = distance(t1, b1)
    ver_dist2 = distance(t2, b2)
    return (ver_dist1 + ver_dist2) / (2.0 * hor_dist)

def get_normalized_mar(landmarks, top_idx, bottom_idx, corner1_idx, corner2_idx, w, h):
    """Calculates the Mouth Aspect Ratio (MAR) for open mouth detection."""
    t = get_landmark_point(landmarks[top_idx], w, h)
    b = get_landmark_point(landmarks[bottom_idx], w, h)
    c1 = get_landmark_point(landmarks[corner1_idx], w, h)
    c2 = get_landmark_point(landmarks[corner2_idx], w, h)
    
    ver_dist = distance(t, b)
    hor_dist = distance(c1, c2)
    if hor_dist == 0:
        return 0
    return ver_dist / hor_dist

def main():
    cap = cv2.VideoCapture(0)
    # Optimize camera settings for high FPS and lower latency
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 60)

    # Create a floating window that stays on top
    cv2.namedWindow('AccessiGaming Cam', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('AccessiGaming Cam', cv2.WND_PROP_TOPMOST, 1)

    # 3D Model Points for head pose estimation (generic face model)
    model_points = np.array([
        (0.0, 0.0, 0.0),             # Nose tip
        (0.0, -330.0, -65.0),        # Chin
        (-225.0, 170.0, -135.0),     # Viewer's left eye corner
        (225.0, 170.0, -135.0),      # Viewer's right eye corner
        (-150.0, -150.0, -125.0),    # Viewer's left mouth corner
        (150.0, -150.0, -125.0)      # Viewer's right mouth corner
    ], dtype=np.float64)

    # Landmark indices for EAR/MAR (Assuming mirrored image)
    LEFT_EYE_CORNERS = [33, 133]  # Left side of image
    LEFT_EYE_TOP = [159, 158]
    LEFT_EYE_BOTTOM = [153, 144]

    RIGHT_EYE_CORNERS = [362, 263] # Right side of image
    RIGHT_EYE_TOP = [386, 385]
    RIGHT_EYE_BOTTOM = [374, 380]

    MOUTH_TOP = 13
    MOUTH_BOTTOM = 14
    MOUTH_CORNERS = [78, 308]

    # State variables
    center_pitch = 0.0
    center_yaw = 0.0
    is_calibrated = False

    left_click_pressed = False
    right_click_pressed = False
    mouth_action_pressed = False
    is_paused = False
    last_pause_time = time.time()

    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as face_mesh:

        while cap.isOpened():
            success, image = cap.read()
            if not success:
                continue

            # Toggle pause with F9
            current_time = time.time()
            if keyboard.is_pressed('F9') and (current_time - last_pause_time) > 0.5:
                is_paused = not is_paused
                last_pause_time = current_time
                if is_paused:
                    print("CAMARA EN PAUSA")
                else:
                    print("CAMARA REANUDADA")

            # Flip the image horizontally for intuitive mirror-like control
            image = cv2.flip(image, 1)
            
            # Improve performance by marking image not writeable during processing
            image.flags.writeable = False
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(image_rgb)

            # Draw the face mesh annotations on the image
            image.flags.writeable = True
            h, w, _ = image.shape

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    # Draw mesh overlay
                    mp_drawing.draw_landmarks(
                        image=image,
                        landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style())

                    landmarks = face_landmarks.landmark

                    # --- HEAD POSE ESTIMATION ---
                    image_points = np.array([
                        get_landmark_point(landmarks[1], w, h),     # Nose tip
                        get_landmark_point(landmarks[152], w, h),   # Chin
                        get_landmark_point(landmarks[33], w, h),    # Viewer's left eye corner
                        get_landmark_point(landmarks[263], w, h),   # Viewer's right eye corner
                        get_landmark_point(landmarks[61], w, h),    # Viewer's left mouth corner
                        get_landmark_point(landmarks[291], w, h)    # Viewer's right mouth corner
                    ], dtype=np.float64)

                    focal_length = w
                    camera_center = (w / 2, h / 2)
                    camera_matrix = np.array(
                        [[focal_length, 0, camera_center[0]],
                         [0, focal_length, camera_center[1]],
                         [0, 0, 1]], dtype=np.float64
                    )
                    dist_coeffs = np.zeros((4, 1))

                    success_pnp, rotation_vector, translation_vector = cv2.solvePnP(
                        model_points, image_points, camera_matrix, dist_coeffs)

                    if success_pnp:
                        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
                        proj_matrix = np.hstack((rotation_matrix, translation_vector))
                        euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)[6]
                        pitch = euler_angles[0][0]
                        yaw = euler_angles[1][0]
                        roll = euler_angles[2][0]

                        # Initial auto-calibration if not calibrated yet
                        if not is_calibrated:
                            center_pitch = pitch
                            center_yaw = yaw
                            is_calibrated = True

                        rel_pitch = pitch - center_pitch
                        rel_yaw = yaw - center_yaw

                        # --- CALCULATE MOUSE MOVEMENT ---
                        if is_paused:
                            if left_click_pressed: pydirectinput.mouseUp(button='left'); left_click_pressed = False
                            if right_click_pressed: pydirectinput.mouseUp(button='right'); right_click_pressed = False
                            if mouth_action_pressed: pydirectinput.keyUp(KEY_MOUTH); mouth_action_pressed = False
                            cv2.putText(image, "PAUSADO (F9 para reanudar)", (10, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                            continue

                        dx = 0
                        dy = 0

                        # Horizontal Movement (Yaw)
                        if rel_yaw > DEADZONE_YAW:
                            dx = (rel_yaw - DEADZONE_YAW) * SENSITIVITY_X
                        elif rel_yaw < -DEADZONE_YAW:
                            dx = (rel_yaw + DEADZONE_YAW) * SENSITIVITY_X

                        # Vertical Movement (Pitch)
                        if rel_pitch > DEADZONE_PITCH:
                            dy = (rel_pitch - DEADZONE_PITCH) * SENSITIVITY_Y
                        elif rel_pitch < -DEADZONE_PITCH:
                            dy = (rel_pitch + DEADZONE_PITCH) * SENSITIVITY_Y

                        if INVERT_X: dx = -dx
                        if INVERT_Y: dy = -dy

                        # Send continuous relative mouse movements
                        if dx != 0 or dy != 0:
                            pydirectinput.move(int(dx), int(dy))

                        # --- FACIAL GESTURES (Blinks & Mouth) ---
                        left_ear = get_ear(landmarks, LEFT_EYE_CORNERS, LEFT_EYE_TOP, LEFT_EYE_BOTTOM, w, h)
                        right_ear = get_ear(landmarks, RIGHT_EYE_CORNERS, RIGHT_EYE_TOP, RIGHT_EYE_BOTTOM, w, h)
                        mar = get_normalized_mar(landmarks, MOUTH_TOP, MOUTH_BOTTOM, MOUTH_CORNERS[0], MOUTH_CORNERS[1], w, h)

                        # Left Blink -> Left Click (Holdable)
                        if left_ear < BLINK_THRESHOLD:
                            if not left_click_pressed:
                                pydirectinput.mouseDown(button='left')
                                left_click_pressed = True
                        else:
                            if left_click_pressed:
                                pydirectinput.mouseUp(button='left')
                                left_click_pressed = False

                        # Right Blink -> Right Click (Holdable)
                        if right_ear < BLINK_THRESHOLD:
                            if not right_click_pressed:
                                pydirectinput.mouseDown(button='right')
                                right_click_pressed = True
                        else:
                            if right_click_pressed:
                                pydirectinput.mouseUp(button='right')
                                right_click_pressed = False

                        # Mouth Open -> Keyboard Action (Holdable)
                        if mar > MOUTH_THRESHOLD:
                            if not mouth_action_pressed:
                                pydirectinput.keyDown(KEY_MOUTH)
                                mouth_action_pressed = True
                        else:
                            if mouth_action_pressed:
                                pydirectinput.keyUp(KEY_MOUTH)
                                mouth_action_pressed = False

                        # --- GUI TEXT & FEEDBACK ---
                        cv2.putText(image, "Press 'C' to Calibrate Center | 'Q' to Quit", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                        cv2.putText(image, f"Pitch: {rel_pitch:.1f} | Yaw: {rel_yaw:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        cv2.putText(image, f"L_EAR: {left_ear:.2f} | R_EAR: {right_ear:.2f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        cv2.putText(image, f"MAR: {mar:.2f}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                        if left_click_pressed:
                            cv2.putText(image, "LEFT CLICK", (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                        if right_click_pressed:
                            cv2.putText(image, "RIGHT CLICK", (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                        if mouth_action_pressed:
                            cv2.putText(image, f"ACTION ({KEY_MOUTH.upper()})", (10, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
            else:
                # Face lost, release inputs safely
                if left_click_pressed: pydirectinput.mouseUp(button='left'); left_click_pressed = False
                if right_click_pressed: pydirectinput.mouseUp(button='right'); right_click_pressed = False
                if mouth_action_pressed: pydirectinput.keyUp(KEY_MOUTH); mouth_action_pressed = False
                cv2.putText(image, "ROSTRO NO DETECTADO", (10, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            # Display the frame
            cv2.imshow('AccessiGaming Cam', image)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                if 'pitch' in locals() and 'yaw' in locals():
                    center_pitch = pitch
                    center_yaw = yaw
                    print("Center calibrated!")

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    # Release any potentially stuck inputs
    pydirectinput.mouseUp(button='left')
    pydirectinput.mouseUp(button='right')
    pydirectinput.keyUp(KEY_MOUTH)

if __name__ == "__main__":
    main()
