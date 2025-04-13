from typing import Optional, Dict, Any
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch

logger = logging.getLogger(__name__)

class HFModelService:
    """Service for handling Hugging Face model operations.
    
    This service provides functionality for loading and using Hugging Face models
    for text generation and conversation.
    """
    
    def __init__(self, model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def load_model(self) -> None:
        """Load the model and tokenizer.
        
        Raises:
            RuntimeError: If model loading fails.
        """
        try:
            logger.info(f"Loading model {self.model_name} on {self.device}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto"
            )
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=self.device
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Failed to load model: {e}")
            
    def generate_response(
        self,
        prompt: str,
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs: Any
    ) -> str:
        """Generate a response using the loaded model.
        
        Args:
            prompt: The input prompt for the model.
            max_length: Maximum length of the generated response.
            temperature: Controls randomness in generation.
            top_p: Controls diversity via nucleus sampling.
            **kwargs: Additional generation parameters.
            
        Returns:
            The generated response text.
            
        Raises:
            RuntimeError: If model is not loaded or generation fails.
        """
        if not self.pipeline:
            raise RuntimeError("Model not loaded. Call load_model() first.")
            
        try:
            response = self.pipeline(
                prompt,
                max_length=max_length,
                temperature=temperature,
                top_p=top_p,
                **kwargs
            )[0]["generated_text"]
            
            # Remove the prompt from the response
            response = response[len(prompt):].strip()
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise RuntimeError(f"Failed to generate response: {e}")
            
    def chat(
        self,
        message: str,
        history: Optional[list[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> str:
        """Generate a chat response with conversation history.
        
        Args:
            message: The user's message.
            history: List of previous messages in the format [{"role": "user", "content": "..."}].
            **kwargs: Additional generation parameters.
            
        Returns:
            The model's response.
        """
        if not history:
            history = []
            
        # Format the conversation history
        formatted_history = "\n".join(
            f"{msg['role']}: {msg['content']}" for msg in history
        )
        
        # Create the prompt with history
        prompt = f"{formatted_history}\nuser: {message}\nassistant:"
        
        return self.generate_response(prompt, **kwargs) 