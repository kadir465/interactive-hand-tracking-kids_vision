import cv2
import numpy as np
import math
import random
import os
import time

class PuzzleGame:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.piece_size = 100 # Adjusted for 6x6 to fit 720p 
        self.snap_threshold = 45 # Slightly smaller snap for smaller piece
        self.pinch_threshold = 65
        
        # Professional UI settings
        self.toolbar_h = 100
        self.colors = {
            "bg": (255, 240, 230), # Soft sky blue-ish
            "accent": (100, 200, 50), # Mint green
            "button": (255, 150, 50), # Bright orange
            "hover": (255, 180, 100),
            "text": (50, 50, 50),
            "white": (255, 255, 255)
        }
        
        self.buttons = [
            {"label": "🤖 Robot", "rect": (50, 20, 200, 80), "action": "theme", "value": "robot"},
            {"label": "🐱 Kedi", "rect": (220, 20, 370, 80), "action": "theme", "value": "cat"},
            {"label": "🔄 Yenile", "rect": (600, 20, 780, 80), "action": "restart", "value": None},
            {"label": "❌ Kapat", "rect": (800, 20, 980, 80), "action": "exit", "value": None}
        ]
        self.hover_timers = [0.0] * len(self.buttons)
        self.active_puzzle_type = "robot"
        
        self.targets = []
        self.pieces = []
        self.selected_piece_idx = -1
        
        # Jigsaw edge settings
        self.tab_size = self.piece_size // 5
        
        self.setup_puzzle(self.active_puzzle_type)

    def _generate_jigsaw_path(self, edges):
        """
        Generates contour points for a jigsaw piece using smooth curves (Bezier approximation).
        edges: list of 4 values (Top, Right, Bottom, Left)
        Values: 0: Flat, 1: Tab (Out), -1: Slot (In)
        """
        s = self.piece_size
        t = self.tab_size
        path = []

        def add_edge(p1, p2, type):
            # p1, p2 are start and end of the edge segment
            v = np.array(p2) - np.array(p1)
            dist = np.linalg.norm(v)
            n = np.array([-v[1], v[0]]) / dist # Perpendicular vector
            
            mid = (np.array(p1) + np.array(p2)) / 2
            
            if type == 0:
                return [p1, p2]
            
            # Create a nice curved tab
            # Points for a rounded tab: neck start, neck curve, head, neck curve, neck end
            q1 = p1 + v * 0.35
            q2 = p1 + v * 0.45 + n * (t * type * 0.2)
            q3 = mid + n * (t * type * 1.0) # Peak
            q4 = p1 + v * 0.55 + n * (t * type * 0.2)
            q5 = p1 + v * 0.65
            
            # Simplified version for efficiency in OpenCV
            res = [p1, q1.astype(int).tolist(), q2.astype(int).tolist(), 
                   q3.astype(int).tolist(), q4.astype(int).tolist(), 
                   q5.astype(int).tolist(), p2]
            return res

        # Corners
        c00, c10, c11, c01 = [0,0], [s,0], [s,s], [0,s]
        
        # Build path clockwise
        path.extend(add_edge(c00, c10, edges[0])) # Top
        path.extend(add_edge(c10, c11, edges[1])) # Right
        path.extend(add_edge(c11, c01, edges[2])) # Bottom
        path.extend(add_edge(c01, c00, edges[3])) # Left
        
        return np.array(path, dtype=np.int32)

    def setup_puzzle(self, puzzle_type):
        self.active_puzzle_type = puzzle_type
        self.pieces = []
        self.targets = []
        
        rows, cols = 6, 6
        grid_w = cols * self.piece_size
        grid_h = rows * self.piece_size
        
        # Center the target grid on the right half of the screen
        start_x = (self.screen_w * 3 // 4) - (grid_w // 2)
        start_y = (self.screen_h // 2) - (grid_h // 2) + (self.toolbar_h // 2)

        # Load image
        img_path = f"assets/{puzzle_type}.png"
        source_img = cv2.imread(img_path)
        
        if source_img is None:
            source_img = np.zeros((grid_h, grid_w, 3), dtype=np.uint8)
            cv2.putText(source_img, "Gorsel Bulunamadi", (50, grid_h//2), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        source_img = cv2.resize(source_img, (grid_w, grid_h))

        # Edge definitions for the grid (shared edges between pieces)
        h_edges = [[0]*cols for _ in range(rows+1)]
        v_edges = [[0]*(cols+1) for _ in range(rows)]
        
        for r in range(1, rows):
            for c in range(cols):
                h_edges[r][c] = random.choice([1, -1])
        for r in range(rows):
            for c in range(1, cols):
                v_edges[r][c] = random.choice([1, -1])

        for r in range(rows):
            for c in range(cols):
                tx = start_x + c * self.piece_size
                ty = start_y + r * self.piece_size
                self.targets.append((tx + self.piece_size//2, ty + self.piece_size//2))
                
                # Piece edges: Top, Right, Bottom, Left
                edges = [
                    -h_edges[r][c], # Top
                    v_edges[r][c+1], # Right
                    h_edges[r+1][c], # Bottom
                    -v_edges[r][c] # Left
                ]
                
                path = self._generate_jigsaw_path(edges)
                
                # Pad for tabs
                pad = self.tab_size + 5
                mask_size = self.piece_size + 2 * pad
                mask = np.zeros((mask_size, mask_size), dtype=np.uint8)
                shifted_path = path + pad
                cv2.fillPoly(mask, [shifted_path], 255)
                
                # Content extraction
                content = np.zeros((mask_size, mask_size, 3), dtype=np.uint8)
                ix, iy = c * self.piece_size, r * self.piece_size
                
                # Sample source with padding
                s1x, s1y = ix - pad, iy - pad
                s2x, s2y = ix + self.piece_size + pad, iy + self.piece_size + pad
                
                samp_x1, samp_y1 = max(0, s1x), max(0, s1y)
                samp_x2, samp_y2 = min(grid_w, s2x), min(grid_h, s2y)
                
                cx1, cy1 = max(0, -s1x), max(0, -s1y)
                cx2, cy2 = cx1 + (samp_x2 - samp_x1), cy1 + (samp_y2 - samp_y1)
                
                content[cy1:cy2, cx1:cx2] = source_img[samp_y1:samp_y2, samp_x1:samp_x2]
                piece_img = cv2.bitwise_and(content, content, mask=mask)
                
                # Multi-color scatter
                rx = random.randint(50, self.screen_w // 3)
                ry = random.randint(self.toolbar_h + 50, self.screen_h - 200)
                
                self.pieces.append({
                    "pos": [rx, ry],
                    "target": (tx, ty),
                    "locked": False,
                    "img": piece_img,
                    "mask": mask,
                    "path": shifted_path,
                    "offset": pad,
                    "grid_pos": (r, c)
                })
        
        self.selected_piece_idx = -1

    def restart(self):
        self.setup_puzzle(self.active_puzzle_type)

    def get_completed_image(self):
        img = np.zeros((self.screen_h, self.screen_w, 3), dtype=np.uint8)
        for piece in self.pieces:
            self._draw_piece(img, piece, piece["target"], locked=True)
        return img

    def _draw_rounded_rect(self, img, rect, color, thickness=-1, radius=15):
        x1, y1, x2, y2 = rect
        # Draw the main body
        if thickness == -1:
            cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, -1)
            cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, -1)
            # Draw circles at corners
            cv2.circle(img, (x1 + radius, y1 + radius), radius, color, -1)
            cv2.circle(img, (x2 - radius, y1 + radius), radius, color, -1)
            cv2.circle(img, (x1 + radius, y2 - radius), radius, color, -1)
            cv2.circle(img, (x2 - radius, y2 - radius), radius, color, -1)
        else:
            # Simple border
            cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
            cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, thickness)
            cv2.circle(img, (x1 + radius, y1 + radius), radius, color, thickness)
            cv2.circle(img, (x2 - radius, y1 + radius), radius, color, thickness)
            cv2.circle(img, (x1 + radius, y2 - radius), radius, color, thickness)
            cv2.circle(img, (x2 - radius, y2 - radius), radius, color, thickness)

    def _draw_piece(self, img, piece, pos, locked=False, selected=False, ghost=False):
        px, py = int(pos[0]), int(pos[1])
        pad = piece["offset"]
        h, w = piece["img"].shape[:2]
        
        x1, y1 = px - pad, py - pad
        x2, y2 = x1 + w, y1 + h
        
        if x1 < 0 or y1 < 0 or x2 > self.screen_w or y2 > self.screen_h:
            # Simple safety: clip piece if it goes out of screen
            x_start = max(0, x1)
            y_start = max(0, y1)
            x_end = min(self.screen_w, x2)
            y_end = min(self.screen_h, y2)
            
            p_start_x = x_start - x1
            p_start_y = y_start - y1
            p_end_x = p_start_x + (x_end - x_start)
            p_end_y = p_start_y + (y_end - y_start)
            
            if x_end <= x_start or y_end <= y_start: return
            
            p_img = piece["img"][p_start_y:p_end_y, p_start_x:p_end_x]
            p_mask = piece["mask"][p_start_y:p_end_y, p_start_x:p_end_x]
            roi = img[y_start:y_end, x_start:x_end]
        else:
            p_img = piece["img"]
            p_mask = piece["mask"]
            roi = img[y1:y2, x1:x2]
            x_start, y_start = x1, y1

        if ghost:
            # Professional Silhouette
            alpha = 0.2
            gray = np.full_like(roi, 100)
            mask_3ch = (p_mask / 255.0).reshape(p_mask.shape[0], p_mask.shape[1], 1)
            ghost_roi = (roi * (1 - alpha * mask_3ch) + gray * (alpha * mask_3ch)).astype(np.uint8)
            img[y_start:y_start+roi.shape[0], x_start:x_start+roi.shape[1]] = ghost_roi
            cv2.polylines(img, [piece["path"] + [px-pad, py-pad]], True, (80, 80, 80), 1)
            return

        mask_inv = cv2.bitwise_not(p_mask)
        bg = cv2.bitwise_and(roi, roi, mask=mask_inv)
        fg = cv2.bitwise_and(p_img, p_img, mask=p_mask)
        
        if locked:
            # Neon Green Success Glow
            glow = np.zeros_like(p_img)
            cv2.polylines(glow, [piece["path"]], True, (0, 255, 0), 4)
            glow = cv2.GaussianBlur(glow, (9, 9), 0)
            fg = cv2.addWeighted(fg, 1.0, glow, 1.5, 0)
        
        if selected:
            # White highlight for selected
            cv2.polylines(fg, [piece["path"]], True, (255, 255, 255), 2)
            
        res = cv2.add(bg, fg)
        img[y_start:y_start+roi.shape[0], x_start:x_start+roi.shape[1]] = res

    def update(self, pinch_score, index_pos=None):
        if index_pos:
            ix, iy = index_pos
            for i, btn in enumerate(self.buttons):
                bx1, by1, bx2, by2 = btn["rect"]
                if bx1 < ix < bx2 and by1 < iy < by2:
                    if self.hover_timers[i] == 0:
                        self.hover_timers[i] = time.time()
                    elif time.time() - self.hover_timers[i] > 1.2:
                        if btn["action"] == "theme":
                            self.setup_puzzle(btn["value"])
                        elif btn["action"] == "restart":
                            self.restart()
                        elif btn["action"] == "exit":
                            return "EXIT"
                        self.hover_timers[i] = 0
                else:
                    self.hover_timers[i] = 0

        if pinch_score is None:
            self.selected_piece_idx = -1
            return False
        
        dist, center = pinch_score
        px, py = center
        
        if self.selected_piece_idx != -1:
            idx = self.selected_piece_idx
            if dist < self.pinch_threshold:
                tx, ty = self.pieces[idx]["target"]
                d_target = math.hypot(px - (tx + self.piece_size//2), py - (ty + self.piece_size//2))
                
                if d_target < self.snap_threshold:
                    self.pieces[idx]["pos"] = [tx, ty]
                    self.pieces[idx]["locked"] = True
                    self.selected_piece_idx = -1
                else:
                    self.pieces[idx]["pos"] = [px - self.piece_size//2, py - self.piece_size//2]
            else:
                self.selected_piece_idx = -1
        else:
            if dist < self.pinch_threshold:
                for i in range(len(self.pieces)-1, -1, -1):
                    p = self.pieces[i]
                    if not p["locked"]:
                        ppx, ppy = p["pos"]
                        pad = p["offset"]
                        mx, my = int(px - ppx + pad), int(py - ppy + pad)
                        # Offset hit test
                        if 0 <= mx < p["mask"].shape[1] and 0 <= my < p["mask"].shape[0]:
                            if p["mask"][my, mx] > 0:
                                self.selected_piece_idx = i
                                item = self.pieces.pop(i)
                                self.pieces.append(item)
                                self.selected_piece_idx = len(self.pieces) - 1
                                break
                                
        return all(p["locked"] for p in self.pieces)

    def draw(self, img):
        # Background
        # cv2.rectangle(img, (0, 80), (self.screen_h, self.screen_w), (20, 20, 20), -1)
        
        # Toolbar
        cv2.rectangle(img, (0, 0), (self.screen_w, self.toolbar_h), self.colors["bg"], -1)
        cv2.line(img, (0, self.toolbar_h), (self.screen_w, self.toolbar_h), (200, 200, 200), 2)
        
        now = time.time()
        for i, btn in enumerate(self.buttons):
            bx1, by1, bx2, by2 = btn["rect"]
            is_active = (btn["action"] == "theme" and self.active_puzzle_type == btn["value"])
            
            # Button BG
            b_color = self.colors["accent"] if is_active else self.colors["button"]
            if self.hover_timers[i] > 0:
                prog = min(1.0, (now - self.hover_timers[i]) / 1.2)
                self._draw_rounded_rect(img, (bx1, by1, bx2, by2), b_color, radius=15)
                # Loading bar on button
                cv2.rectangle(img, (bx1 + 10, by2 - 10), (bx1 + 10 + int((bx2 - bx1 - 20) * prog), by2 - 5), 
                            self.colors["white"], -1)
            else:
                self._draw_rounded_rect(img, (bx1, by1, bx2, by2), b_color, radius=15)
            
            # Button border
            self._draw_rounded_rect(img, (bx1, by1, bx2, by2), self.colors["white"], thickness=2, radius=15)
            
            # Label
            label_color = self.colors["white"]
            cv2.putText(img, btn["label"], (bx1 + 20, by1 + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, label_color, 2, cv2.LINE_AA)

        # Silhouette
        for p in self.pieces:
            self._draw_piece(img, p, p["target"], ghost=True)
            
        # Pieces
        for i, p in enumerate(self.pieces):
            if i == self.selected_piece_idx: continue
            self._draw_piece(img, p, p["pos"], locked=p["locked"])
            
        if self.selected_piece_idx != -1:
            p = self.pieces[self.selected_piece_idx]
            self._draw_piece(img, p, p["pos"], selected=True)
            
        cv2.putText(img, f"MinikCoder Puzzle: {self.active_puzzle_type.title()}", (self.screen_w - 350, 45), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 2, cv2.LINE_AA)
