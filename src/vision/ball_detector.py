"""
Ball Detection Module

Detects the soccer ball in camera images using color and shape detection.

Author: Team 1
Date: October 2025
"""

import numpy as np
import cv2
from typing import Optional, Tuple, Dict


class BallDetector:
    """
    Detects orange/white soccer ball in camera images.
    
    Uses color filtering and Hough circle detection to identify
    the ball and estimate its position relative to the robot.
    """
    
    def __init__(self):
        """Initialize ball detector with default parameters."""
        # Color ranges for orange ball (HSV)
        self.orange_lower = np.array([5, 100, 100])
        self.orange_upper = np.array([15, 255, 255])
        
        # Color ranges for white ball (HSV)
        self.white_lower = np.array([0, 0, 200])
        self.white_upper = np.array([180, 30, 255])
        
        # Detection parameters
        self.min_ball_radius = 10  # pixels
        self.max_ball_radius = 100  # pixels
        self.confidence_threshold = 0.7
        
    def detect(self, image: np.ndarray) -> Optional[Dict]:
        """
        Detect ball in image.
        
        Args:
            image: BGR image from camera
            
        Returns:
            Dictionary with ball information or None if not detected:
            {
                'center': (x, y) pixel coordinates,
                'radius': radius in pixels,
                'confidence': detection confidence,
                'distance': estimated distance in meters,
                'angle': angle from robot center in radians
            }
        """
        if image is None or image.size == 0:
            return None
            
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Try detecting orange ball
        ball_info = self._detect_colored_ball(image, hsv, 
                                             self.orange_lower, 
                                             self.orange_upper)
        
        # If no orange ball, try white
        if ball_info is None:
            ball_info = self._detect_colored_ball(image, hsv,
                                                 self.white_lower,
                                                 self.white_upper)
        
        return ball_info
    
    def _detect_colored_ball(self, image: np.ndarray, hsv: np.ndarray,
                            lower: np.array, upper: np.array) -> Optional[Dict]:
        """
        Detect ball of specific color range.
        
        Args:
            image: Original BGR image
            hsv: HSV converted image
            lower: Lower HSV threshold
            upper: Upper HSV threshold
            
        Returns:
            Ball information dictionary or None
        """
        # Create mask for color
        mask = cv2.inRange(hsv, lower, upper)
        
        # Apply morphological operations to remove noise
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Find circles using Hough transform
        circles = cv2.HoughCircles(
            mask,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=50,
            param2=30,
            minRadius=self.min_ball_radius,
            maxRadius=self.max_ball_radius
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            
            # Get the most prominent circle (first one)
            for circle in circles[0, :1]:
                x, y, r = circle
                
                # Calculate confidence based on circularity
                confidence = self._calculate_confidence(mask, x, y, r)
                
                if confidence > self.confidence_threshold:
                    # Estimate distance and angle
                    distance = self._estimate_distance(r)
                    angle = self._estimate_angle(x, image.shape[1])
                    
                    return {
                        'center': (int(x), int(y)),
                        'radius': int(r),
                        'confidence': confidence,
                        'distance': distance,
                        'angle': angle
                    }
        
        return None
    
    def _calculate_confidence(self, mask: np.ndarray, x: int, y: int, 
                            r: int) -> float:
        """
        Calculate detection confidence based on mask coverage.
        
        Args:
            mask: Binary mask image
            x, y: Circle center coordinates
            r: Circle radius
            
        Returns:
            Confidence value between 0 and 1
        """
        # Create circular mask
        h, w = mask.shape
        Y, X = np.ogrid[:h, :w]
        dist_from_center = np.sqrt((X - x)**2 + (Y - y)**2)
        circle_mask = dist_from_center <= r
        
        # Calculate how much of the circle is filled
        circle_area = np.sum(circle_mask)
        if circle_area == 0:
            return 0.0
            
        filled_area = np.sum(mask[circle_mask] > 0)
        confidence = filled_area / circle_area
        
        return confidence
    
    def _estimate_distance(self, radius_pixels: int) -> float:
        """
        Estimate ball distance from its apparent size.
        
        Args:
            radius_pixels: Ball radius in pixels
            
        Returns:
            Estimated distance in meters
        """
        # This is a simplified model - should be calibrated
        # Assumes ball diameter of 14cm and camera parameters
        BALL_DIAMETER = 0.14  # meters
        FOCAL_LENGTH = 500  # pixels (approximate)
        
        if radius_pixels > 0:
            distance = (BALL_DIAMETER * FOCAL_LENGTH) / (2 * radius_pixels)
            return min(max(distance, 0.1), 10.0)  # Clamp to reasonable range
        
        return 5.0  # Default distance
    
    def _estimate_angle(self, x_pixels: int, image_width: int) -> float:
        """
        Estimate angle to ball from image position.
        
        Args:
            x_pixels: X coordinate in image
            image_width: Total image width
            
        Returns:
            Angle in radians (positive = left, negative = right)
        """
        # Camera field of view (approximate)
        FOV = np.radians(60)  # 60 degrees FOV
        
        # Normalize x position to [-1, 1]
        x_normalized = (2.0 * x_pixels / image_width) - 1.0
        
        # Calculate angle
        angle = x_normalized * (FOV / 2)
        
        return -angle  # Flip sign for intuitive direction
    
    def draw_detection(self, image: np.ndarray, ball_info: Dict) -> np.ndarray:
        """
        Draw ball detection on image for visualization.
        
        Args:
            image: Image to draw on
            ball_info: Ball detection information
            
        Returns:
            Image with detection drawn
        """
        if ball_info is None:
            return image
            
        result = image.copy()
        
        # Draw circle
        cv2.circle(result, ball_info['center'], ball_info['radius'],
                  (0, 255, 0), 2)
        
        # Draw center point
        cv2.circle(result, ball_info['center'], 3, (0, 0, 255), -1)
        
        # Add text information
        text = f"Dist: {ball_info['distance']:.2f}m"
        cv2.putText(result, text, 
                   (ball_info['center'][0] - 40, ball_info['center'][1] - ball_info['radius'] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return result
