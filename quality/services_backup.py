"""
Quality Analysis Services using YOLO for Agricultural Products
"""
import cv2
import numpy as np
from PIL import Image, ImageStat
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import os
from django.conf import settings

logger = logging.getLogger(__name__)

class YOLOQualityAnalyzer:
    """YOLO-based quality analyzer for agricultural products"""
    
    def __init__(self):
        self.model = None
        self.confidence_threshold = getattr(settings, 'QUALITY_SCORE_THRESHOLD', 0.5)
        self.quality_grades = getattr(settings, 'QUALITY_GRADES', {
            'A': {'min_score': 0.8, 'label': 'Premium Quality'},
            'B': {'min_score': 0.6, 'label': 'Good Quality'},
            'C': {'min_score': 0.4, 'label': 'Average Quality'},
            'D': {'min_score': 0.0, 'label': 'Below Average Quality'},
        })
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model for quality analysis"""
        try:
            # Try to import ultralytics
            from ultralytics import YOLO
            
            model_path = getattr(settings, 'YOLO_MODEL_PATH', None)
            if model_path and os.path.exists(model_path):
                self.model = YOLO(model_path)
                logger.info(f"Loaded custom YOLO model from {model_path}")
            else:
                # Use a pre-trained model for object detection
                self.model = YOLO('yolov8n.pt')  # Nano model for faster processing
                logger.info("Loaded pre-trained YOLOv8 nano model")
                
        except ImportError:
            logger.warning("Ultralytics not available, using fallback analysis")
            self.model = None
        except Exception as e:
            logger.error(f"Error loading YOLO model: {e}")
            self.model = None
    
    def analyze_image(self, image_path: str) -> Dict:
        """
        Analyze product image for quality assessment
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing quality analysis results
        """
        try:
            start_time = datetime.now()
            
            # Load and process image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Initialize results
            results = {
                'overall_score': 0.0,
                'quality_grade': 'D',
                'size_score': 0.0,
                'color_score': 0.0,
                'shape_score': 0.0,
                'surface_score': 0.0,
                'freshness_score': 0.0,
                'defects_detected': [],
                'defect_count': 0,
                'defect_severity': 'none',
                'bounding_boxes': [],
                'class_predictions': [],
                'confidence_scores': [],
                'estimated_weight': None,
                'ripeness_level': 'unknown',
                'shelf_life_days': None,
                'processing_time': 0.0,
                'error_message': ''
            }
            
            # YOLO detection
            if self.model:
                yolo_results = self._run_yolo_detection(image)
                results.update(yolo_results)
            
            # Color analysis
            color_analysis = self._analyze_color(image)
            results.update(color_analysis)
            
            # Shape and size analysis
            shape_analysis = self._analyze_shape_and_size(image)
            results.update(shape_analysis)
            
            # Surface quality analysis
            surface_analysis = self._analyze_surface_quality(image)
            results.update(surface_analysis)
            
            # Calculate overall score
            results['overall_score'] = self._calculate_overall_score(results)
            results['quality_grade'] = self._determine_quality_grade(results['overall_score'])
            
            # Calculate processing time
            end_time = datetime.now()
            results['processing_time'] = (end_time - start_time).total_seconds()
            
            logger.info(f"Image analysis completed: Grade {results['quality_grade']}, Score {results['overall_score']:.2f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {e}")
            return {
                'overall_score': 0.0,
                'quality_grade': 'D',
                'error_message': str(e),
                'processing_time': 0.0
            }
    
    def _run_yolo_detection(self, image: np.ndarray) -> Dict:
        """Run YOLO detection on the image"""
        results = {
            'bounding_boxes': [],
            'class_predictions': [],
            'confidence_scores': [],
            'defects_detected': []
        }
        
        try:
            if self.model is None:
                return results
            
            # Run inference
            detections = self.model(image)
            
            # Extract results
            for detection in detections:
                if detection.boxes is not None:
                    boxes = detection.boxes.xyxy.cpu().numpy()  # Bounding boxes
                    confidences = detection.boxes.conf.cpu().numpy()  # Confidence scores
                    classes = detection.boxes.cls.cpu().numpy()  # Class IDs
                    
                    for i, (box, conf, cls) in enumerate(zip(boxes, confidences, classes)):
                        if conf > self.confidence_threshold:
                            results['bounding_boxes'].append(box.tolist())
                            results['confidence_scores'].append(float(conf))
                            
                            # Get class name
                            class_name = self.model.names[int(cls)] if hasattr(self.model, 'names') else f"class_{int(cls)}"
                            results['class_predictions'].append(class_name)
                            
                            # Check for defects (based on class names or confidence)
                            if self._is_defect(class_name, conf):
                                results['defects_detected'].append({
                                    'type': class_name,
                                    'confidence': float(conf),
                                    'bbox': box.tolist()
                                })
            
        except Exception as e:
            logger.error(f"YOLO detection error: {e}")
        
        return results
    
    def _analyze_color(self, image: np.ndarray) -> Dict:
        """Analyze color properties of the produce"""
        try:
            # Convert to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            # Calculate color statistics
            stat = ImageStat.Stat(pil_image)
            
            # Get dominant colors
            mean_colors = stat.mean
            
            # Convert to HSV for better analysis
            hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Calculate color uniformity
            h_channel = hsv_image[:, :, 0]
            s_channel = hsv_image[:, :, 1]
            v_channel = hsv_image[:, :, 2]
            
            h_std = np.std(h_channel)
            s_std = np.std(s_channel)
            v_std = np.std(v_channel)
            
            # Calculate color score based on uniformity and brightness
            color_uniformity = 1.0 - min(h_std / 180.0, 1.0)  # Normalize hue std
            brightness_score = min(np.mean(v_channel) / 255.0, 1.0)
            saturation_score = min(np.mean(s_channel) / 255.0, 1.0)
            
            color_score = (color_uniformity * 0.4 + brightness_score * 0.3 + saturation_score * 0.3)
            
            # Determine ripeness based on color
            ripeness = self._determine_ripeness(mean_colors, hsv_image)
            
            return {
                'color_score': min(max(color_score, 0.0), 1.0),
                'ripeness_level': ripeness,
                'mean_rgb': [float(c) for c in mean_colors],
                'color_uniformity': color_uniformity
            }
            
        except Exception as e:
            logger.error(f"Color analysis error: {e}")
            return {'color_score': 0.5, 'ripeness_level': 'unknown'}
    
    def _analyze_shape_and_size(self, image: np.ndarray) -> Dict:
        """Analyze shape regularity and size estimation"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to get binary image
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return {'shape_score': 0.5, 'size_score': 0.5, 'estimated_weight': None}
            
            # Get the largest contour (assuming it's the main product)
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            perimeter = cv2.arcLength(largest_contour, True)
            
            # Calculate shape metrics
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter ** 2)
                circularity = min(circularity, 1.0)
            else:
                circularity = 0.0
            
            # Calculate aspect ratio
            x, y, w, h = cv2.boundingRect(largest_contour)
            aspect_ratio = min(w, h) / max(w, h) if max(w, h) > 0 else 0
            
            # Shape score combines circularity and aspect ratio
            shape_score = (circularity * 0.6 + aspect_ratio * 0.4)
            
            # Size score based on area (normalized)
            image_area = image.shape[0] * image.shape[1]
            size_ratio = area / image_area if image_area > 0 else 0
            size_score = min(size_ratio * 2, 1.0)  # Assume good size is ~50% of image
            
            # Estimate weight (very rough approximation)
            estimated_weight = self._estimate_weight(area, shape_score)
            
            return {
                'shape_score': min(max(shape_score, 0.0), 1.0),
                'size_score': min(max(size_score, 0.0), 1.0),
                'estimated_weight': estimated_weight,
                'circularity': circularity,
                'aspect_ratio': aspect_ratio,
                'area_pixels': int(area)
            }
            
        except Exception as e:
            logger.error(f"Shape analysis error: {e}")
            return {'shape_score': 0.5, 'size_score': 0.5, 'estimated_weight': None}
    
    def _analyze_surface_quality(self, image: np.ndarray) -> Dict:
        """Analyze surface quality for defects and blemishes"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Calculate texture using standard deviation
            texture_score = np.std(blurred) / 255.0
            
            # Detect edges (potential defects)
            edges = cv2.Canny(blurred, 50, 150)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            
            # Calculate surface smoothness
            laplacian_var = cv2.Laplacian(blurred, cv2.CV_64F).var()
            smoothness = 1.0 - min(laplacian_var / 1000.0, 1.0)  # Normalize
            
            # Surface score combines texture and smoothness
            surface_score = (smoothness * 0.7 + (1.0 - edge_density) * 0.3)
            
            # Freshness estimation based on surface quality
            freshness_score = surface_score * 0.8 + texture_score * 0.2
            
            return {
                'surface_score': min(max(surface_score, 0.0), 1.0),
                'freshness_score': min(max(freshness_score, 0.0), 1.0),
                'texture_variance': texture_score,
                'smoothness': smoothness,
                'edge_density': edge_density
            }
            
        except Exception as e:
            logger.error(f"Surface analysis error: {e}")
            return {'surface_score': 0.5, 'freshness_score': 0.5}
    
    def _calculate_overall_score(self, results: Dict) -> float:
        """Calculate overall quality score from individual metrics"""
        # Weights for different factors
        weights = {
            'size_score': 0.2,
            'color_score': 0.25,
            'shape_score': 0.2,
            'surface_score': 0.25,
            'freshness_score': 0.1
        }
        
        overall_score = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            if metric in results and results[metric] is not None:
                overall_score += results[metric] * weight
                total_weight += weight
        
        # Penalize for defects
        defect_penalty = len(results.get('defects_detected', [])) * 0.1
        overall_score = max(0.0, overall_score - defect_penalty)
        
        return min(overall_score, 1.0) if total_weight > 0 else 0.0
    
    def _determine_quality_grade(self, score: float) -> str:
        """Determine quality grade based on score"""
        for grade, criteria in self.quality_grades.items():
            if score >= criteria['min_score']:
                return grade
        return 'D'
    
    def _determine_ripeness(self, rgb_colors: List[float], hsv_image: np.ndarray) -> str:
        """Determine ripeness level based on color analysis"""
        # This is a simplified ripeness detection
        # In practice, this would be more sophisticated and product-specific
        
        try:
            # Get average hue
            avg_hue = np.mean(hsv_image[:, :, 0])
            avg_saturation = np.mean(hsv_image[:, :, 1])
            avg_value = np.mean(hsv_image[:, :, 2])
            
            # Simple heuristics for common fruits/vegetables
            if avg_value < 100:  # Very dark
                return 'overripe'
            elif avg_saturation > 150 and avg_value > 150:  # High saturation and brightness
                return 'ripe'
            elif avg_saturation < 100:  # Low saturation
                return 'underripe'
            else:
                return 'ripe'
                
        except Exception:
            return 'unknown'
    
    def _estimate_weight(self, area_pixels: float, shape_score: float) -> Optional[float]:
        """Estimate weight based on visual features"""
        # This is a very rough estimation
        # In practice, you'd need calibration data and ML models
        
        try:
            # Assume a calibration factor (would need real data)
            base_weight = area_pixels / 10000.0  # Rough conversion
            shape_factor = 0.5 + shape_score * 0.5  # Better shape = denser
            
            estimated_weight = base_weight * shape_factor
            return round(estimated_weight, 2) if estimated_weight > 0 else None
            
        except Exception:
            return None
    
    def _is_defect(self, class_name: str, confidence: float) -> bool:
        """Determine if a detected object represents a defect"""
        defect_keywords = [
            'spot', 'blemish', 'bruise', 'rot', 'mold', 'damage',
            'crack', 'hole', 'discoloration', 'decay'
        ]
        
        class_lower = class_name.lower()
        return any(keyword in class_lower for keyword in defect_keywords)

# Service functions for Django integration

def analyze_product_image(image_path: str) -> Dict:
    """
    Main function to analyze a product image
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Analysis results dictionary
    """
    analyzer = YOLOQualityAnalyzer()
    return analyzer.analyze_image(image_path)

def batch_analyze_images(image_paths: List[str]) -> List[Dict]:
    """
    Analyze multiple images in batch
    
    Args:
        image_paths: List of image file paths
        
    Returns:
        List of analysis results
    """
    analyzer = YOLOQualityAnalyzer()
    results = []
    
    for image_path in image_paths:
        result = analyzer.analyze_image(image_path)
        result['image_path'] = image_path
        results.append(result)
    
    return results

def get_quality_summary(analysis_results: List[Dict]) -> Dict:
    """
    Generate quality summary from multiple analysis results
    
    Args:
        analysis_results: List of analysis result dictionaries
        
    Returns:
        Summary statistics
    """
    if not analysis_results:
        return {}
    
    scores = [r.get('overall_score', 0) for r in analysis_results]
    grades = [r.get('quality_grade', 'D') for r in analysis_results]
    
    summary = {
        'total_analyses': len(analysis_results),
        'average_score': sum(scores) / len(scores) if scores else 0,
        'max_score': max(scores) if scores else 0,
        'min_score': min(scores) if scores else 0,
        'grade_distribution': {
            'A': grades.count('A'),
            'B': grades.count('B'),
            'C': grades.count('C'),
            'D': grades.count('D')
        },
        'most_common_grade': max(set(grades), key=grades.count) if grades else 'D'
    }
    
    return summary
