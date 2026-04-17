import cv2
import numpy as np
import time

class DrawingGame:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.path = [] 
        self.piece_size = 90
        self.grid_rows, self.grid_cols = 6, 6
        self.is_finished = False
        
        # Geometry sync with puzzle
        self.grid_w = self.grid_cols * self.piece_size
        self.grid_h = self.grid_rows * self.piece_size
        self.right_start_x = (3 * self.screen_w // 4) - (self.grid_w // 2)
        self.start_y = (self.screen_h // 2) - (self.grid_h // 2) + (80 // 2)
        
        # Professional UI settings
        self.toolbar_h = 100
        self.colors = {
            "bg": (230, 245, 255), # Soft sky blue
            "button": (255, 120, 80), # Coral
            "accent": (100, 200, 50), # Mint
            "text": (50, 50, 50),
            "white": (255, 255, 255),
            "pencil": (0, 0, 255),
            "eraser": (200, 200, 200)
        }
        self.active_tool = "pencil"
        self.active_color = (0, 0, 255) # Red
        self.template_img = None
        
        self.buttons = [
            {"label": "✏️ Kalem", "rect": (30, 20, 160, 80), "type": "tool", "value": "pencil"},
            {"label": "🧽 Silgi", "rect": (175, 20, 305, 80), "type": "tool", "value": "eraser"},
            {"label": "🔴", "rect": (330, 20, 400, 80), "type": "color", "value": (0, 0, 255)},
            {"label": "🟢", "rect": (410, 20, 480, 80), "type": "color", "value": (0, 255, 0)},
            {"label": "🔵", "rect": (490, 20, 560, 80), "type": "color", "value": (255, 0, 0)},
            {"label": "🔄 Yenile", "rect": (630, 20, 800, 80), "type": "action", "value": "restart"},
            {"label": "✅ Bitir", "rect": (830, 20, 1000, 80), "type": "action", "value": "finish"}
        ]
        self.hover_timers = [0.0] * len(self.buttons)

    def set_template(self, img):
        self.template_img = img

    def restart(self):
        self.path = []
        self.is_finished = False
        self.template_img = None

    def update(self, index_pos):
        if index_pos:
            x, y = index_pos
            
            # 1. Check Toolbar
            for i, btn in enumerate(self.buttons):
                bx1, by1, bx2, by2 = btn["rect"]
                if bx1 < x < bx2 and by1 < y < by2:
                    if self.hover_timers[i] == 0:
                        self.hover_timers[i] = time.time()
                    elif time.time() - self.hover_timers[i] > 1.0: # 1s hover
                        if btn["type"] == "tool":
                            self.active_tool = btn["value"]
                        elif btn["type"] == "color":
                            self.active_color = btn["value"]
                        elif btn["type"] == "action":
                            return btn["value"]
                        self.hover_timers[i] = 0
                else:
                    self.hover_timers[i] = 0

            # 2. Handle Drawing/Erasing (Restrict to right grid area)
            gx1, gy1 = self.right_start_x, self.start_y
            gx2, gy2 = gx1 + self.grid_w, gy1 + self.grid_h
            
            if gx1 < x < gx2 and gy1 < y < gy2:
                if self.active_tool == "pencil":
                    self.path.append({"pos": (x, y), "color": self.active_color})
                elif self.active_tool == "eraser":
                    radius = 30
                    self.path = [p for p in self.path if np.linalg.norm(np.array(p["pos"]) - np.array((x, y))) > radius]
                
        return False 

    def _draw_rounded_rect(self, img, rect, color, thickness=-1, radius=15):
        x1, y1, x2, y2 = rect
        if thickness == -1:
            cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, -1)
            cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, -1)
            cv2.circle(img, (x1 + radius, y1 + radius), radius, color, -1)
            cv2.circle(img, (x2 - radius, y1 + radius), radius, color, -1)
            cv2.circle(img, (x1 + radius, y2 - radius), radius, color, -1)
            cv2.circle(img, (x2 - radius, y2 - radius), radius, color, -1)
        else:
            cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
            cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, thickness)
            cv2.circle(img, (x1 + radius, y1 + radius), radius, color, thickness)
            cv2.circle(img, (x2 - radius, y1 + radius), radius, color, thickness)
            cv2.circle(img, (x1 + radius, y2 - radius), radius, color, thickness)
            cv2.circle(img, (x2 - radius, y2 - radius), radius, color, thickness)

    def draw(self, img):
        # 1. Draw Reference Puzzle (on the left side)
        if self.template_img is not None:
            # The template_img already has the puzzle in the target grid position
            # Use semi-transparent blending for tracing
            mask = cv2.cvtColor(self.template_img, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)
            mask_3ch = (mask / 255.0).reshape(mask.shape[0], mask.shape[1], 1)
            alpha = 0.3
            blended = (img * (1 - alpha * mask_3ch) + self.template_img * (alpha * mask_3ch)).astype(np.uint8)
            img[:] = blended

        # 2. Draw Drawing Area Guides (on the right side)
        gx1, gy1 = self.right_start_x, self.start_y
        cv2.rectangle(img, (gx1, gy1), (gx1 + self.grid_w, gy1 + self.grid_h), (150, 150, 150), 2)
        # Draw faint grid
        for r in range(self.grid_rows + 1):
            y = gy1 + r * self.piece_size
            cv2.line(img, (gx1, y), (gx1 + self.grid_w, y), (80, 80, 80), 1)
        for c in range(self.grid_cols + 1):
            x = gx1 + c * self.piece_size
            cv2.line(img, (x, gy1), (x, gy1 + self.grid_h), (80, 80, 80), 1)

        # Draw Toolbar
        cv2.rectangle(img, (0, 0), (self.screen_w, self.toolbar_h), self.colors["bg"], -1)
        cv2.line(img, (0, self.toolbar_h), (self.screen_w, self.toolbar_h), (200, 200, 200), 2)
        
        now = time.time()
        for i, btn in enumerate(self.buttons):
            bx1, by1, bx2, by2 = btn["rect"]
            is_active = False
            if btn["type"] == "tool": is_active = self.active_tool == btn["value"]
            elif btn["type"] == "color": is_active = self.active_color == btn["value"]
            
            b_color = self.colors["accent"] if is_active else self.colors["button"]
            
            # Draw Button
            if self.hover_timers[i] > 0:
                prog = min(1.0, (now - self.hover_timers[i]) / 1.0)
                self._draw_rounded_rect(img, (bx1, by1, bx2, by2), b_color, radius=15)
                # Loading bar
                cv2.rectangle(img, (bx1 + 10, by2 - 12), (bx1 + 10 + int((bx2-bx1-20)*prog), by2 - 7), self.colors["white"], -1)
            else:
                self._draw_rounded_rect(img, (bx1, by1, bx2, by2), b_color, radius=15)
            
            self._draw_rounded_rect(img, (bx1, by1, bx2, by2), self.colors["white"], thickness=2, radius=15)
            
            if btn["type"] == "color":
                cv2.circle(img, (bx1 + (bx2-bx1)//2, by1 + 50), 20, btn["value"], -1)
                cv2.circle(img, (bx1 + (bx2-bx1)//2, by1 + 50), 23, self.colors["white"], 2)
            else:
                cv2.putText(img, btn["label"], (bx1 + 15, by1 + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.colors["white"], 2)


        # Draw translucent separator
        cv2.line(img, (self.screen_w // 2, self.toolbar_h), (self.screen_w // 2, self.screen_h), (255, 255, 255), 2)
        
        # Draw UI text
        cv2.putText(img, "Bak ve Ciz!", (self.right_start_x, self.start_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
        # Draw the path
        if len(self.path) > 1:
            for i in range(1, len(self.path)):
                p1 = self.path[i-1]
                p2 = self.path[i]
                # Only draw line if they are consecutive and same-ish color (to avoid jumps after erasing)
                # Actually, simpler: just draw if distance is small
                if np.linalg.norm(np.array(p1["pos"]) - np.array(p2["pos"])) < 50:
                    cv2.line(img, p1["pos"], p2["pos"], p1["color"], 6, cv2.LINE_AA)

