import os
from ultralytics import YOLO
from typing import Optional, Dict, Any
import logging

class ModelManager:
    """Manages YOLO model loading and switching."""
    
    def __init__(self):
        self.weapon_model: Optional[YOLO] = None
        self.fire_smoke_model: Optional[YOLO] = None
        self.current_model: str = "weapon"
        self.logger = logging.getLogger(__name__)
    
    def load_models(self) -> Dict[str, Any]:
        """Load all configured models from disk."""
        try:
            weapon_model_path = os.getenv("MODEL_WEAPON_PATH", "models/weapon.pt")
            fire_smoke_model_path = os.getenv("MODEL_FIRE_SMOKE_PATH", "models/fire_smoke.pt")
            
            # Load weapon model
            if os.path.exists(weapon_model_path):
                self.weapon_model = YOLO(weapon_model_path)
                self.logger.info(f"Weapon model loaded from {weapon_model_path}")
            else:
                self.logger.warning(f"Weapon model not found at {weapon_model_path}")
                
            # Load fire/smoke model
            if os.path.exists(fire_smoke_model_path):
                self.fire_smoke_model = YOLO(fire_smoke_model_path)
                self.logger.info(f"Fire/Smoke model loaded from {fire_smoke_model_path}")
            else:
                self.logger.warning(f"Fire/Smoke model not found at {fire_smoke_model_path}")
                
            return {
                "weapon_loaded": self.weapon_model is not None,
                "fire_smoke_loaded": self.fire_smoke_model is not None
            }
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            return {
                "weapon_loaded": False,
                "fire_smoke_loaded": False,
                "error": str(e)
            }
    
    def get_current_model(self) -> Optional[YOLO]:
        """Get the currently selected model."""
        if self.current_model == "weapon" and self.weapon_model:
            return self.weapon_model
        elif self.current_model == "fire_smoke" and self.fire_smoke_model:
            return self.fire_smoke_model
        return None
    
    def get_model(self, model_name: str) -> Optional[YOLO]:
        """Get a specific model by name."""
        if model_name == "weapon":
            return self.weapon_model
        elif model_name == "fire_smoke":
            return self.fire_smoke_model
        return None
    
    def models_loaded(self) -> bool:
        """Check if any models are loaded."""
        return self.weapon_model is not None or self.fire_smoke_model is not None
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to a different model."""
        if model_name in ["weapon", "fire_smoke"]:
            self.current_model = model_name
            return True
        return False
    
    def get_available_models(self) -> list:
        """Get list of available models."""
        models = []
        if self.weapon_model:
            models.append("weapon")
        if self.fire_smoke_model:
            models.append("fire_smoke")
        return models