"""
Advanced Quality Analysis Services for AgriMart Platform
Handles YOLO-based image analysis and quality assessment
"""
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import os
import logging
import json
from typing import Dict, List, Tuple, Optional, Any
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
import math

logger = logging.getLogger(__name__)

class YOLOQualityAnalyzer:
    """Advanced YOLO-based quality analyzer for agricultural products"""
    
    def __init__(self):
        self.model = None
        self.confidence_threshold = getattr(settings, 'YOLO_CONFIDENCE_THRESHOLD', 0.5)
        self.load_model()
        
        # Define product-specific quality parameters
        self.product_standards = {
            'apple': {
                'ideal_color_range': [(0, 100, 100), (10, 255, 255)],  # Red range in HSV
                'size_range': (5000, 50000),  # Area in pixels
                'shape_circularity': 0.7,
                'defect_tolerance': 0.1
            },
            'tomato': {
                'ideal_color_range': [(0, 100, 100), (15, 255, 255)],  # Red range
                'size_range': (3000, 30000),
                'shape_circularity': 0.8,
                'defect_tolerance': 0.05
            },
            'banana': {
                'ideal_color_range': [(20, 100, 100), (30, 255, 255)],  # Yellow range
                'size_range': (8000, 40000),
                'shape_circularity': 0.3,  # Elongated shape
                'defect_tolerance': 0.15
            },
            'orange': {
                'ideal_color_range': [(10, 100, 100), (25, 255, 255)],  # Orange range
                'size_range': (4000, 35000),
                'shape_circularity': 0.75,
                'defect_tolerance': 0.1
            },
            'cabbage': {
                'ideal_color_range': [(50, 50, 50), (80, 255, 255)],  # Green range
                'size_range': (10000, 80000),
                'shape_circularity': 0.6,
                'defect_tolerance': 0.2
            },
            'potato': {
                'ideal_color_range': [(15, 30, 80), (25, 100, 200)],  # Brown range
                'size_range': (2000, 25000),
                'shape_circularity': 0.5,
                'defect_tolerance': 0.3
            }
        }
    
    def load_model(self):
        """Load YOLO model for object detection"""
        try:
            # Try to load actual YOLO model
            try:
                from ultralytics import YOLO
                model_path = getattr(settings, 'YOLO_MODEL_PATH', None)
                
                if model_path and os.path.exists(model_path):
                    self.model = YOLO(model_path)
                    logger.info(f"YOLO model loaded from {model_path}")
                else:
                    # Use pre-trained YOLOv8 model
                    self.model = YOLO('yolov8n.pt')  # nano version for speed
                    logger.info("Using pre-trained YOLOv8n model")
                    
            except ImportError:
                logger.warning("Ultralytics not available, using placeholder model")
                self.model = "placeholder_model"
                
        except Exception as e:
            logger.error(f"Error loading YOLO model: {e}")
            self.model = "placeholder_model"
    
    def analyze_image(self, image_path: str, product_type: str = 'generic') -> Dict:
        """Comprehensive image quality analysis using YOLO and computer vision"""
        try:
            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                return {'error': 'Could not load image'}
            
            # Get image metadata
            image_info = self._get_image_info(image_path)
            
            # Detect objects using YOLO (if available)
            objects = self._detect_objects(image)
            
            # Analyze image quality
            quality_metrics = self._comprehensive_quality_analysis(image, product_type)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(quality_metrics, objects, product_type)
            
            # Generate detailed analysis
            analysis_result = {
                'overall_score': overall_score,
                'grade': self._get_quality_grade(overall_score),
                'image_info': image_info,
                'objects_detected': objects,
                'quality_metrics': quality_metrics,
                'defects': self._detect_defects(image, product_type),
                'color_analysis': self._advanced_color_analysis(image, product_type),
                'size_analysis': self._advanced_size_analysis(image),
                'freshness_indicators': self._analyze_freshness(image, product_type),
                'recommendations': self._generate_recommendations(quality_metrics, product_type),
                'timestamp': timezone.now().isoformat()
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {'error': str(e)}
    
    def _get_image_info(self, image_path: str) -> Dict:
        """Extract image metadata"""
        try:
            with Image.open(image_path) as img:
                return {
                    'dimensions': img.size,
                    'format': img.format,
                    'mode': img.mode,
                    'file_size': os.path.getsize(image_path)
                }
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            return {}
    
    def _detect_objects(self, image: np.ndarray) -> List[Dict]:
        """Detect objects using YOLO model"""
        objects = []
        
        try:
            if isinstance(self.model, str):  # Placeholder model
                # Simulate object detection for demo
                objects.append({
                    'class': 'fruit',
                    'confidence': 0.85,
                    'bbox': [100, 100, 200, 200],
                    'center': [150, 150]
                })
            else:
                # Use actual YOLO model
                results = self.model(image)
                
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            confidence = float(box.conf[0])
                            if confidence >= self.confidence_threshold:
                                bbox = box.xyxy[0].tolist()
                                class_id = int(box.cls[0])
                                class_name = self.model.names[class_id]
                                
                                objects.append({
                                    'class': class_name,
                                    'confidence': confidence,
                                    'bbox': bbox,
                                    'center': [(bbox[0] + bbox[2])/2, (bbox[1] + bbox[3])/2]
                                })
                                
        except Exception as e:
            logger.error(f"Error in object detection: {e}")
        
        return objects
    
    def _comprehensive_quality_analysis(self, image: np.ndarray, product_type: str) -> Dict:
        """Perform comprehensive quality analysis"""
        metrics = {}
        
        # Image quality metrics
        metrics['sharpness'] = self._calculate_sharpness(image)
        metrics['brightness'] = self._calculate_brightness(image)
        metrics['contrast'] = self._calculate_contrast(image)
        metrics['saturation'] = self._calculate_saturation(image)
        metrics['noise_level'] = self._calculate_noise_level(image)
        
        # Composition metrics
        metrics['focus_quality'] = self._analyze_focus_quality(image)
        metrics['lighting_quality'] = self._analyze_lighting_quality(image)
        metrics['background_uniformity'] = self._analyze_background(image)
        
        # Product-specific metrics
        if product_type in self.product_standards:
            metrics['color_accuracy'] = self._analyze_color_accuracy(image, product_type)
            metrics['size_appropriateness'] = self._analyze_size_appropriateness(image, product_type)
            metrics['shape_regularity'] = self._analyze_shape_regularity(image, product_type)
        
        return metrics
    
    def _calculate_sharpness(self, image: np.ndarray) -> float:
        """Calculate image sharpness using Laplacian variance"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        # Normalize to 0-100 scale
        return min(100, laplacian_var / 10)
    
    def _calculate_brightness(self, image: np.ndarray) -> float:
        """Calculate average brightness"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray))
    
    def _calculate_contrast(self, image: np.ndarray) -> float:
        """Calculate image contrast"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return float(np.std(gray))
    
    def _calculate_saturation(self, image: np.ndarray) -> float:
        """Calculate color saturation"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        return float(np.mean(hsv[:,:,1]))
    
    def _calculate_noise_level(self, image: np.ndarray) -> float:
        """Estimate noise level in image"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Apply Gaussian blur and calculate difference
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        noise = cv2.absdiff(gray, blurred)
        return float(np.mean(noise))
    
    def _analyze_focus_quality(self, image: np.ndarray) -> float:
        """Analyze focus quality using gradient magnitude"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        return float(np.mean(gradient_magnitude))
    
    def _analyze_lighting_quality(self, image: np.ndarray) -> float:
        """Analyze lighting quality and uniformity"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        
        # Check for proper distribution
        non_zero_bins = np.count_nonzero(hist)
        distribution_score = non_zero_bins / 256 * 100
        
        # Check for overexposure/underexposure
        overexposed = np.sum(hist[240:]) / np.sum(hist) * 100
        underexposed = np.sum(hist[:15]) / np.sum(hist) * 100
        
        exposure_penalty = max(overexposed, underexposed)
        
        return max(0, distribution_score - exposure_penalty)
    
    def _analyze_background(self, image: np.ndarray) -> float:
        """Analyze background uniformity"""
        # Convert to LAB color space for better background detection
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Use edge detection to find foreground objects
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Dilate edges to create mask
        kernel = np.ones((10,10), np.uint8)
        mask = cv2.dilate(edges, kernel, iterations=2)
        
        # Invert mask to get background
        background_mask = cv2.bitwise_not(mask)
        
        # Calculate background uniformity
        if np.sum(background_mask) > 0:
            background_pixels = lab[background_mask > 0]
            if len(background_pixels) > 100:
                std_dev = np.std(background_pixels, axis=0)
                uniformity = 100 - np.mean(std_dev)
                return max(0, uniformity)
        
        return 50  # Default score if can't analyze background
    
    def _analyze_color_accuracy(self, image: np.ndarray, product_type: str) -> float:
        """Analyze color accuracy for specific product type"""
        if product_type not in self.product_standards:
            return 75  # Default score
        
        standards = self.product_standards[product_type]
        ideal_range = standards['ideal_color_range']
        
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Create mask for ideal color range
        mask = cv2.inRange(hsv, np.array(ideal_range[0]), np.array(ideal_range[1]))
        
        # Calculate percentage of pixels in ideal range
        ideal_pixels = np.sum(mask > 0)
        total_pixels = mask.size
        
        color_accuracy = (ideal_pixels / total_pixels) * 100
        return min(100, color_accuracy * 2)  # Scale up for better distribution
    
    def _analyze_size_appropriateness(self, image: np.ndarray, product_type: str) -> float:
        """Analyze if product size is appropriate"""
        if product_type not in self.product_standards:
            return 75
        
        size_analysis = self._advanced_size_analysis(image)
        if 'area' in size_analysis:
            area = size_analysis['area']
            min_size, max_size = self.product_standards[product_type]['size_range']
            
            if min_size <= area <= max_size:
                return 100
            elif area < min_size:
                return max(0, 100 - ((min_size - area) / min_size * 100))
            else:
                return max(0, 100 - ((area - max_size) / max_size * 100))
        
        return 50
    
    def _analyze_shape_regularity(self, image: np.ndarray, product_type: str) -> float:
        """Analyze shape regularity for product type"""
        if product_type not in self.product_standards:
            return 75
        
        size_analysis = self._advanced_size_analysis(image)
        if 'circularity' in size_analysis:
            actual_circularity = size_analysis['circularity']
            expected_circularity = self.product_standards[product_type]['shape_circularity']
            
            # Calculate deviation from expected shape
            deviation = abs(actual_circularity - expected_circularity)
            shape_score = max(0, 100 - (deviation * 100))
            
            return shape_score
        
        return 50
    
    def _detect_defects(self, image: np.ndarray, product_type: str) -> List[Dict]:
        """Detect various types of defects"""
        defects = []
        
        # Convert to different color spaces for defect detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect dark spots (potential rot/bruises)
        defects.extend(self._detect_dark_spots(hsv, gray))
        
        # Detect color inconsistencies
        defects.extend(self._detect_color_inconsistencies(hsv))
        
        # Detect surface blemishes
        defects.extend(self._detect_surface_blemishes(lab))
        
        # Detect wrinkles/texture issues
        defects.extend(self._detect_texture_issues(gray))
        
        return defects
    
    def _detect_dark_spots(self, hsv: np.ndarray, gray: np.ndarray) -> List[Dict]:
        """Detect dark spots indicating rot or bruises"""
        defects = []
        
        # Threshold for dark areas
        dark_mask = cv2.inRange(gray, 0, 60)
        
        # Find contours
        contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        significant_spots = 0
        total_dark_area = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # Filter small noise
                significant_spots += 1
                total_dark_area += area
        
        if significant_spots > 0:
            defects.append({
                'type': 'dark_spots',
                'severity': 'high' if significant_spots > 5 else 'medium',
                'count': significant_spots,
                'total_area': total_dark_area
            })
        
        return defects
    
    def _detect_color_inconsistencies(self, hsv: np.ndarray) -> List[Dict]:
        """Detect color inconsistencies"""
        defects = []
        
        # Calculate color variance in hue channel
        hue_std = np.std(hsv[:,:,0])
        
        if hue_std > 30:  # High color variance
            defects.append({
                'type': 'color_inconsistency',
                'severity': 'medium',
                'variance': float(hue_std)
            })
        
        return defects
    
    def _detect_surface_blemishes(self, lab: np.ndarray) -> List[Dict]:
        """Detect surface blemishes using LAB color space"""
        defects = []
        
        # Use A and B channels to detect unusual color patches
        a_channel = lab[:,:,1]
        b_channel = lab[:,:,2]
        
        # Find extreme values that might indicate blemishes
        a_extreme = np.logical_or(a_channel < 100, a_channel > 155)
        b_extreme = np.logical_or(b_channel < 100, b_channel > 155)
        
        extreme_areas = np.logical_or(a_extreme, b_extreme)
        blemish_percentage = np.sum(extreme_areas) / extreme_areas.size * 100
        
        if blemish_percentage > 5:
            defects.append({
                'type': 'surface_blemishes',
                'severity': 'high' if blemish_percentage > 15 else 'medium',
                'percentage': float(blemish_percentage)
            })
        
        return defects
    
    def _detect_texture_issues(self, gray: np.ndarray) -> List[Dict]:
        """Detect texture issues like wrinkles"""
        defects = []
        
        # Apply Gabor filter to detect texture patterns
        kernel = cv2.getGaborKernel((15, 15), 3, 0, 10, 0.5, 0, ktype=cv2.CV_32F)
        gabor_response = cv2.filter2D(gray, cv2.CV_8UC3, kernel)
        
        # Calculate texture energy
        texture_energy = np.mean(gabor_response**2)
        
        if texture_energy > 1000:  # High texture variation
            defects.append({
                'type': 'texture_irregularity',
                'severity': 'low',
                'energy': float(texture_energy)
            })
        
        return defects
    
    def _advanced_color_analysis(self, image: np.ndarray, product_type: str) -> Dict:
        """Advanced color analysis with multiple color spaces"""
        # Convert to different color spaces
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # HSV analysis
        hsv_stats = {
            'mean_hue': float(np.mean(hsv[:,:,0])),
            'mean_saturation': float(np.mean(hsv[:,:,1])),
            'mean_value': float(np.mean(hsv[:,:,2])),
            'hue_std': float(np.std(hsv[:,:,0])),
            'saturation_std': float(np.std(hsv[:,:,1])),
            'value_std': float(np.std(hsv[:,:,2]))
        }
        
        # LAB analysis
        lab_stats = {
            'lightness': float(np.mean(lab[:,:,0])),
            'a_component': float(np.mean(lab[:,:,1])),
            'b_component': float(np.mean(lab[:,:,2])),
            'color_uniformity': float(np.std(lab, axis=(0,1)).mean())
        }
        
        # Color histogram analysis
        color_distribution = self._analyze_color_distribution(hsv)
        
        # Dominant colors
        dominant_colors = self._extract_dominant_colors(image)
        
        return {
            'hsv_analysis': hsv_stats,
            'lab_analysis': lab_stats,
            'color_distribution': color_distribution,
            'dominant_colors': dominant_colors,
            'color_complexity': self._calculate_color_complexity(hsv)
        }
    
    def _analyze_color_distribution(self, hsv: np.ndarray) -> Dict:
        """Analyze color distribution in HSV space"""
        hue_hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        sat_hist = cv2.calcHist([hsv], [1], None, [256], [0, 256])
        val_hist = cv2.calcHist([hsv], [2], None, [256], [0, 256])
        
        return {
            'hue_peaks': len([i for i, v in enumerate(hue_hist) if v[0] > np.max(hue_hist) * 0.1]),
            'saturation_peak': float(np.argmax(sat_hist)),
            'value_peak': float(np.argmax(val_hist)),
            'color_spread': float(np.std(hue_hist))
        }
    
    def _extract_dominant_colors(self, image: np.ndarray, k: int = 3) -> List[Dict]:
        """Extract dominant colors using K-means clustering"""
        try:
            # Reshape image to be a list of pixels
            pixels = image.reshape((-1, 3))
            pixels = np.float32(pixels)
            
            # Apply K-means
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convert centers to uint8 and calculate percentages
            centers = np.uint8(centers)
            dominant_colors = []
            
            for i, color in enumerate(centers):
                percentage = np.sum(labels == i) / len(labels) * 100
                dominant_colors.append({
                    'color_bgr': color.tolist(),
                    'percentage': float(percentage)
                })
            
            return sorted(dominant_colors, key=lambda x: x['percentage'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error extracting dominant colors: {e}")
            return []
    
    def _calculate_color_complexity(self, hsv: np.ndarray) -> float:
        """Calculate color complexity score"""
        # Calculate entropy of hue channel
        hue_hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        hue_hist = hue_hist.flatten()
        hue_hist = hue_hist[hue_hist > 0]  # Remove zeros
        
        if len(hue_hist) > 0:
            # Normalize
            hue_hist = hue_hist / np.sum(hue_hist)
            # Calculate entropy
            entropy = -np.sum(hue_hist * np.log2(hue_hist + 1e-10))
            return float(entropy)
        
        return 0.0
    
    def _advanced_size_analysis(self, image: np.ndarray) -> Dict:
        """Advanced size and shape analysis"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Edge detection and contour finding
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {'error': 'No objects detected'}
        
        # Find largest contour (main object)
        main_contour = max(contours, key=cv2.contourArea)
        
        # Calculate various metrics
        area = cv2.contourArea(main_contour)
        perimeter = cv2.arcLength(main_contour, True)
        
        # Bounding rectangle
        x, y, w, h = cv2.boundingRect(main_contour)
        aspect_ratio = w / h if h > 0 else 0
        
        # Minimum enclosing circle
        (cx, cy), radius = cv2.minEnclosingCircle(main_contour)
        
        # Convex hull
        hull = cv2.convexHull(main_contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        
        # Circularity
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        # Moments for centroid
        moments = cv2.moments(main_contour)
        if moments['m00'] > 0:
            centroid_x = moments['m10'] / moments['m00']
            centroid_y = moments['m01'] / moments['m00']
        else:
            centroid_x = centroid_y = 0
        
        return {
            'area': float(area),
            'perimeter': float(perimeter),
            'aspect_ratio': float(aspect_ratio),
            'circularity': float(circularity),
            'solidity': float(solidity),
            'bounding_box': {
                'x': int(x), 'y': int(y), 
                'width': int(w), 'height': int(h)
            },
            'enclosing_circle': {
                'center': [float(cx), float(cy)], 
                'radius': float(radius)
            },
            'centroid': [float(centroid_x), float(centroid_y)]
        }
    
    def _analyze_freshness(self, image: np.ndarray, product_type: str) -> Dict:
        """Analyze freshness indicators"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Color-based freshness (varies by product)
        freshness_indicators = {
            'color_vibrancy': float(np.mean(hsv[:,:,1])),  # Saturation
            'brightness': float(np.mean(hsv[:,:,2])),      # Value
            'color_uniformity': 100 - float(np.std(hsv[:,:,0])),  # Hue consistency
        }
        
        # Detect browning/wilting (common freshness indicators)
        brown_mask = cv2.inRange(hsv, np.array([10, 50, 50]), np.array([20, 255, 200]))
        brown_percentage = np.sum(brown_mask > 0) / brown_mask.size * 100
        
        freshness_indicators['browning_percentage'] = float(brown_percentage)
        
        # Calculate overall freshness score
        freshness_score = (
            freshness_indicators['color_vibrancy'] * 0.3 +
            freshness_indicators['brightness'] * 0.2 +
            freshness_indicators['color_uniformity'] * 0.3 +
            max(0, 100 - brown_percentage * 2) * 0.2
        ) / 100 * 100
        
        freshness_indicators['freshness_score'] = min(100, max(0, freshness_score))
        
        return freshness_indicators
    
    def _calculate_overall_score(self, metrics: Dict, objects: List[Dict], product_type: str) -> float:
        """Calculate comprehensive quality score"""
        score_components = []
        
        # Image quality components (40% weight)
        if 'sharpness' in metrics:
            score_components.append(('sharpness', metrics['sharpness'] * 0.1))
        if 'brightness' in metrics:
            # Normalize brightness (optimal around 120-140)
            brightness_score = 100 - abs(metrics['brightness'] - 130) * 2
            score_components.append(('brightness', max(0, brightness_score) * 0.1))
        if 'contrast' in metrics:
            # Normalize contrast (optimal around 50-80)
            contrast_score = 100 - abs(metrics['contrast'] - 65) * 1.5
            score_components.append(('contrast', max(0, contrast_score) * 0.1))
        if 'lighting_quality' in metrics:
            score_components.append(('lighting', metrics['lighting_quality'] * 0.1))
        
        # Product-specific components (40% weight)
        if 'color_accuracy' in metrics:
            score_components.append(('color_accuracy', metrics['color_accuracy'] * 0.2))
        if 'size_appropriateness' in metrics:
            score_components.append(('size', metrics['size_appropriateness'] * 0.1))
        if 'shape_regularity' in metrics:
            score_components.append(('shape', metrics['shape_regularity'] * 0.1))
        
        # Object detection confidence (10% weight)
        if objects:
            avg_confidence = np.mean([obj['confidence'] for obj in objects]) * 100
            score_components.append(('detection', avg_confidence * 0.1))
        
        # Background quality (10% weight)
        if 'background_uniformity' in metrics:
            score_components.append(('background', metrics['background_uniformity'] * 0.1))
        
        # Calculate weighted average
        total_score = sum(score for _, score in score_components)
        
        # Apply penalties for specific issues
        penalty = 0
        if 'noise_level' in metrics and metrics['noise_level'] > 20:
            penalty += (metrics['noise_level'] - 20) * 0.5
        
        final_score = max(0, min(100, total_score - penalty))
        
        return round(final_score, 2)
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to grade with detailed criteria"""
        grades = getattr(settings, 'QUALITY_GRADES', {
            'A': {'min_score': 85, 'name': 'Premium'},
            'B': {'min_score': 70, 'name': 'Good'},
            'C': {'min_score': 50, 'name': 'Fair'},
            'D': {'min_score': 0, 'name': 'Poor'},
        })
        
        for grade, criteria in sorted(grades.items(), 
                                    key=lambda x: x[1]['min_score'], 
                                    reverse=True):
            if score >= criteria['min_score']:
                return grade
        return 'D'
    
    def _generate_recommendations(self, metrics: Dict, product_type: str) -> List[str]:
        """Generate specific recommendations based on analysis"""
        recommendations = []
        
        # Image quality recommendations
        if metrics.get('sharpness', 0) < 50:
            recommendations.append("Use a tripod or stabilize camera to reduce blur")
            recommendations.append("Ensure proper focus on the main subject")
        
        if metrics.get('lighting_quality', 0) < 60:
            recommendations.append("Improve lighting conditions - use natural light or additional lighting")
            recommendations.append("Avoid harsh shadows and direct flash")
        
        if metrics.get('background_uniformity', 0) < 70:
            recommendations.append("Use a plain, neutral background")
            recommendations.append("Remove clutter from the background")
        
        # Product-specific recommendations
        if metrics.get('color_accuracy', 0) < 70:
            recommendations.append("Ensure accurate color representation")
            recommendations.append("Check white balance settings")
        
        if metrics.get('noise_level', 0) > 20:
            recommendations.append("Reduce ISO settings to minimize noise")
            recommendations.append("Use better lighting instead of high ISO")
        
        # Composition recommendations
        recommendations.append("Center the product in the frame")
        recommendations.append("Ensure the entire product is visible")
        recommendations.append("Take multiple angles for better representation")
        
        return recommendations

# Service functions
def analyze_product_image(image_file, product_type: str = 'generic', product=None) -> Dict:
    """Analyze product image and return comprehensive quality assessment"""
    try:
        # Save uploaded image temporarily
        temp_path = default_storage.save(
            f'temp/analysis_{timezone.now().strftime("%Y%m%d_%H%M%S")}_{image_file.name}', 
            ContentFile(image_file.read())
        )
        full_path = default_storage.path(temp_path)
        
        # Analyze with YOLO
        analyzer = YOLOQualityAnalyzer()
        analysis_result = analyzer.analyze_image(full_path, product_type)
        
        # Clean up temporary file
        default_storage.delete(temp_path)
        
        # Add product context if available
        if product:
            analysis_result['product_context'] = {
                'name': product.name,
                'category': product.category.name if hasattr(product, 'category') else 'Unknown',
                'expected_quality': getattr(product, 'expected_quality_grade', 'B')
            }
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error in product image analysis: {e}")
        return {'error': str(e)}

def batch_analyze_images(image_paths: List[str], product_type: str = 'generic') -> List[Dict]:
    """Analyze multiple images in batch with progress tracking"""
    analyzer = YOLOQualityAnalyzer()
    results = []
    
    for i, image_path in enumerate(image_paths):
        try:
            result = analyzer.analyze_image(image_path, product_type)
            results.append({
                'image_path': image_path,
                'analysis': result,
                'batch_index': i + 1,
                'total_images': len(image_paths)
            })
        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {e}")
            results.append({
                'image_path': image_path,
                'analysis': {'error': str(e)},
                'batch_index': i + 1,
                'total_images': len(image_paths)
            })
    
    return results

def get_quality_insights(analysis_results: List[Dict]) -> Dict:
    """Generate insights from multiple quality analyses"""
    if not analysis_results:
        return {}
    
    # Extract scores and grades
    scores = []
    grades = {}
    defect_types = {}
    
    for result in analysis_results:
        if 'analysis' in result and 'overall_score' in result['analysis']:
            scores.append(result['analysis']['overall_score'])
            
            grade = result['analysis'].get('grade', 'D')
            grades[grade] = grades.get(grade, 0) + 1
            
            for defect in result['analysis'].get('defects', []):
                defect_type = defect.get('type', 'unknown')
                defect_types[defect_type] = defect_types.get(defect_type, 0) + 1
    
    if not scores:
        return {'error': 'No valid analysis results'}
    
    insights = {
        'summary': {
            'total_images': len(analysis_results),
            'average_score': round(np.mean(scores), 2),
            'score_std': round(np.std(scores), 2),
            'min_score': min(scores),
            'max_score': max(scores)
        },
        'grade_distribution': grades,
        'common_defects': sorted(defect_types.items(), key=lambda x: x[1], reverse=True),
        'quality_trend': 'improving' if len(scores) > 1 and scores[-1] > scores[0] else 'stable',
        'recommendations': []
    }
    
    # Generate insights-based recommendations
    if insights['summary']['average_score'] < 70:
        insights['recommendations'].append("Overall quality needs improvement")
        insights['recommendations'].append("Focus on better photography techniques")
    
    if 'dark_spots' in defect_types and defect_types['dark_spots'] > len(scores) * 0.3:
        insights['recommendations'].append("Address product freshness and handling")
    
    return insights
