import cv2
import numpy as np
import time
import random
from src.hand_tracker import HandTracker
from src.puzzle_logic import PuzzleGame
from src.drawing_logic import DrawingGame

# Physical distance marker would be ~1-1.5m away as per ground tape instruction
# Ring light on the computer is recommended for better hand detection

class MainApp:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        self.screen_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.screen_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.tracker = HandTracker(detection_conf=0.75, track_conf=0.75)
        self.puzzle = PuzzleGame(self.screen_w, self.screen_h) 
        self.drawing = DrawingGame(self.screen_w, self.screen_h)
        
        self.state = 0 # 0: Puzzle, 1: Drawing, 2: Celeb
        self.celebration_start_time = 0
        self.confetti_particles = []

    def setup_window(self):
        cv2.namedWindow('Uygulama', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('Uygulama', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def generate_confetti(self):
        for _ in range(150):
            x = random.randint(0, self.screen_w)
            y = random.randint(-self.screen_h, 0)
            color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
            speed = random.randint(7, 20)
            self.confetti_particles.append({'pos': [x, y], 'color': color, 'speed': speed})

    def draw_confetti(self, img):
        for p in self.confetti_particles:
            p['pos'][1] += p['speed']
            cv2.circle(img, (p['pos'][0], p['pos'][1]), 5, p['color'], -1)
        # Clear particles off screen
        self.confetti_particles = [p for p in self.confetti_particles if p['pos'][1] < self.screen_h]

    def run(self):
        self.setup_window()
        while True:
            success, frame = self.cap.read()
            if not success:
                break
            
            # Mirror effect (CRITICAL for hand-eye coordination)
            frame = cv2.flip(frame, 1)
            
            # Find hands
            frame = self.tracker.find_hands(frame)
            lm_list = self.tracker.get_landmarks(frame)
            
            if self.state == 0: # Puzzle Mode
                pinch_score = self.tracker.get_pinch_score(lm_list)
                index_pos = self.tracker.get_index_pos(lm_list)
                result = self.puzzle.update(pinch_score, index_pos)
                
                if result == "EXIT":
                    break
                    
                self.puzzle.draw(frame)
                if result is True: # Puzzle finished
                    print("Puzzle Finished! Moving to Drawing.")
                    # Capture completed image and pass to drawing
                    puzzle_img = self.puzzle.get_completed_image()
                    self.drawing.set_template(puzzle_img)
                    
                    self.state = 1
                    time.sleep(1) # Small pause
            
            elif self.state == 1: # Drawing Mode
                index_pos = self.tracker.get_index_pos(lm_list)
                result = self.drawing.update(index_pos)
                
                if result == "restart":
                    self.state = 0
                    self.puzzle.restart()
                    self.drawing.restart()
                    continue
                if result == "exit":
                    break
                elif result == "exit" or result == "exit_app": # result from toolbar
                    break
                
                if result == "finish" or (len(self.drawing.path) > 1000 and result is False):
                    self.state = 2
                    self.celebration_start_time = time.time()
                    self.generate_confetti()
                    
                self.drawing.draw(frame)
            
            elif self.state == 2: # Celebration and Reset
                # Soft overlay for celebration
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (self.screen_w, self.screen_h), (255, 200, 150), -1)
                cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
                
                self.draw_confetti(frame)
                
                # Draw "TEBRİKLER" with shadow
                text = "HARIKA IS CIKARDIN! 🎉"
                font = cv2.FONT_HERSHEY_SIMPLEX
                scale = 2.5
                thick = 8
                (tw, th), _ = cv2.getTextSize(text, font, scale, thick)
                tx, ty = (self.screen_w - tw)//2, (self.screen_h + th)//2
                
                cv2.putText(frame, text, (tx+5, ty+5), font, scale, (50, 50, 50), thick) # Shadow
                cv2.putText(frame, text, (tx, ty), font, scale, (255, 255, 255), thick) # Main text
                
                # Reset after 3 seconds
                if time.time() - self.celebration_start_time > 3:
                    self.state = 0
                    self.puzzle.restart()
                    self.drawing.restart()
                    self.confetti_particles = []
            
            cv2.imshow('Uygulama', frame)
            
            key = cv2.waitKey(1)
            if key == ord('q'):
                break
            if key == ord('r'): # Force restart
                self.state = 0
                self.puzzle.restart()
                self.drawing.restart()

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = MainApp()
    app.run()
