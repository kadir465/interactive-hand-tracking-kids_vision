import cv2
import mediapipe as mp
import math

class HandTracker:
    def __init__(self, mode=False, max_hands=2, detection_conf=0.7, track_conf=0.7):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=mode,
            max_num_hands=max_hands,
            min_detection_confidence=detection_conf,
            min_tracking_confidence=track_conf
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.results = None

    def find_hands(self, img, draw=True):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)
        
        if self.results.multi_hand_landmarks and draw:
            for hand_lms in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)
        return img

    def get_landmarks(self, img, hand_idx=0):
        lm_list = []
        if self.results and self.results.multi_hand_landmarks:
            if len(self.results.multi_hand_landmarks) > hand_idx:
                hand = self.results.multi_hand_landmarks[hand_idx]
                h, w, c = img.shape
                for id, lm in enumerate(hand.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append([id, cx, cy])
        return lm_list

    def get_pinch_score(self, lm_list):
        """Returns the distance between thumb (4) and index (8) tips."""
        if len(lm_list) < 9:
            return None
        
        x1, y1 = lm_list[4][1], lm_list[4][2] # Thumb tip
        x2, y2 = lm_list[8][1], lm_list[8][2] # Index tip
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        
        length = math.hypot(x2 - x1, y2 - y1)
        return length, [cx, cy]

    def get_index_pos(self, lm_list):
        """Returns the [x, y] position of index finger tip (8)."""
        if len(lm_list) < 9:
            return None
        return [lm_list[8][1], lm_list[8][2]]
