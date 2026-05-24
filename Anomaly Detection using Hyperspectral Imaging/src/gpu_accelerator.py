"""
GPU Acceleration Module
Provides GPU acceleration support for faster inference and training
"""

import numpy as np
import torch
from typing import Optional, Dict, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GPUAccelerator:
    """
    Manages GPU acceleration for model operations
    """
    
    def __init__(self, device: Optional[str] = None):
        """
        Initialize GPU accelerator
        
        Args:
            device: Device to use ('cuda', 'cpu', or None for auto-detect)
        """
        if device is None:
            self.device = self._detect_device()
        else:
            self.device = device
        
        self.gpu_available = torch.cuda.is_available()
        self.gpu_count = torch.cuda.device_count() if self.gpu_available else 0
        self.gpu_name = torch.cuda.get_device_name(0) if self.gpu_available else "N/A"
        
        if self.gpu_available:
            print(f"GPU detected: {self.gpu_name}")
            print(f"Using device: {self.device}")
        else:
            print("No GPU detected, using CPU")
    
    def _detect_device(self) -> str:
        """Auto-detect best available device"""
        if torch.cuda.is_available():
            return 'cuda'
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return 'mps'  # Apple Silicon
        else:
            return 'cpu'
    
    def get_device(self) -> torch.device:
        """Get the current device"""
        return torch.device(self.device)
    
    def to_device(self, data: Any) -> Any:
        """
        Move data to the configured device
        
        Args:
            data: Tensor, model, or other PyTorch object
            
        Returns:
            Data moved to device
        """
        if isinstance(data, (torch.Tensor, torch.nn.Module)):
            return data.to(self.device)
        return data
    
    def get_memory_info(self) -> Dict[str, float]:
        """
        Get GPU memory information
        
        Returns:
            Dictionary with memory stats in GB
        """
        if not self.gpu_available:
            return {'available': 0, 'used': 0, 'total': 0}
        
        allocated = torch.cuda.memory_allocated(0) / 1024**3
        reserved = torch.cuda.memory_reserved(0) / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        
        return {
            'allocated': allocated,
            'reserved': reserved,
            'total': total,
            'available': total - reserved
        }
    
    def clear_cache(self):
        """Clear GPU cache"""
        if self.gpu_available:
            torch.cuda.empty_cache()
    
    def set_memory_fraction(self, fraction: float):
        """
        Set GPU memory fraction to use
        
        Args:
            fraction: Fraction of GPU memory to use (0.0 to 1.0)
        """
        if self.gpu_available:
            torch.cuda.set_per_process_memory_fraction(fraction)
    
    def enable_mixed_precision(self) -> bool:
        """
        Enable automatic mixed precision for faster training
        
        Returns:
            Whether mixed precision is enabled
        """
        if self.gpu_available and torch.cuda.is_bf16_supported():
            return True
        return False
    
    def benchmark_device(self, size: int = 1000) -> Dict[str, float]:
        """
        Benchmark device performance
        
        Args:
            size: Size of test tensor
            
        Returns:
            Dictionary with benchmark results
        """
        import time
        
        # Create test data
        x = torch.randn(size, size).to(self.device)
        y = torch.randn(size, size).to(self.device)
        
        # Warmup
        for _ in range(10):
            _ = torch.matmul(x, y)
        
        if self.gpu_available:
            torch.cuda.synchronize()
        
        # Benchmark
        start = time.time()
        for _ in range(100):
            _ = torch.matmul(x, y)
        
        if self.gpu_available:
            torch.cuda.synchronize()
        
        elapsed = time.time() - start
        
        return {
            'device': self.device,
            'matrix_size': size,
            'iterations': 100,
            'total_time': elapsed,
            'avg_time_per_op': elapsed / 100,
            'ops_per_second': 100 / elapsed
        }


class BatchProcessor:
    """
    Process data in batches for GPU efficiency
    """
    
    def __init__(self, batch_size: int = 32, device: str = 'cuda'):
        self.batch_size = batch_size
        self.device = device
        self.accelerator = GPUAccelerator(device)
    
    def process_in_batches(
        self,
        data: np.ndarray,
        process_fn,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Process data in batches
        
        Args:
            data: Input data (N, ...)
            process_fn: Function to process each batch
            show_progress: Show progress bar
            
        Returns:
            Processed data
        """
        N = data.shape[0]
        results = []
        
        for i in range(0, N, self.batch_size):
            batch = data[i:i + self.batch_size]
            batch_tensor = torch.FloatTensor(batch).to(self.accelerator.device)
            
            # Process batch
            result = process_fn(batch_tensor)
            
            # Move back to CPU
            if isinstance(result, torch.Tensor):
                result = result.cpu().numpy()
            
            results.append(result)
            
            if show_progress and (i // self.batch_size) % 10 == 0:
                print(f"Processed {min(i + self.batch_size, N)}/{N} samples")
        
        return np.concatenate(results, axis=0)


class ModelOptimizer:
    """
    Optimize models for faster inference
    """
    
    def __init__(self, device: str = 'cuda'):
        self.device = device
        self.accelerator = GPUAccelerator(device)
    
    def optimize_model(self, model: torch.nn.Module) -> torch.nn.Module:
        """
        Optimize model for inference
        
        Args:
            model: PyTorch model
            
        Returns:
            Optimized model
        """
        model = model.to(self.accelerator.device)
        model.eval()
        
        # Try different optimization techniques
        try:
            # Try TorchScript compilation
            model = torch.jit.script(model)
            print("Model compiled with TorchScript")
        except Exception as e:
            print(f"TorchScript compilation failed: {e}")
        
        try:
            # Try ONNX export (for deployment)
            # This would require additional setup
            pass
        except Exception as e:
            print(f"ONNX export failed: {e}")
        
        return model
    
    def quantize_model(self, model: torch.nn.Module) -> torch.nn.Module:
        """
        Quantize model for faster inference and lower memory
        
        Args:
            model: PyTorch model
            
        Returns:
            Quantized model
        """
        try:
            # Dynamic quantization
            quantized_model = torch.quantization.quantize_dynamic(
                model,
                {torch.nn.Linear, torch.nn.Conv2d},
                dtype=torch.qint8
            )
            print("Model quantized to INT8")
            return quantized_model
        except Exception as e:
            print(f"Quantization failed: {e}")
            return model


class DataLoaderGPU:
    """
    GPU-accelerated data loading and preprocessing
    """
    
    def __init__(self, device: str = 'cuda', num_workers: int = 4):
        self.device = device
        self.num_workers = num_workers
        self.accelerator = GPUAccelerator(device)
    
    def load_and_preprocess(
        self,
        data: np.ndarray,
        normalize: bool = True,
        augment: bool = False
    ) -> torch.Tensor:
        """
        Load and preprocess data on GPU
        
        Args:
            data: Input data
            normalize: Whether to normalize
            augment: Whether to apply augmentation
            
        Returns:
            Preprocessed tensor on GPU
        """
        # Convert to tensor
        tensor = torch.FloatTensor(data).to(self.accelerator.device)
        
        # Normalize
        if normalize:
            mean = tensor.mean()
            std = tensor.std()
            tensor = (tensor - mean) / (std + 1e-8)
        
        # Augmentation (simplified)
        if augment:
            if torch.rand(1) > 0.5:
                tensor = torch.flip(tensor, dims=[1])  # Horizontal flip
            if torch.rand(1) > 0.5:
                tensor = torch.flip(tensor, dims=[2])  # Vertical flip
        
        return tensor


if __name__ == "__main__":
    print("Testing GPU Acceleration...")
    
    # Initialize accelerator
    accelerator = GPUAccelerator()
    
    # Print device info
    print(f"Device: {accelerator.device}")
    print(f"GPU Available: {accelerator.gpu_available}")
    print(f"GPU Count: {accelerator.gpu_count}")
    print(f"GPU Name: {accelerator.gpu_name}")
    
    # Get memory info
    memory = accelerator.get_memory_info()
    print(f"Memory Info: {memory}")
    
    # Benchmark
    benchmark = accelerator.benchmark_device(size=500)
    print(f"Benchmark: {benchmark}")
    
    # Test batch processing
    batch_processor = BatchProcessor(batch_size=32, device=accelerator.device)
    
    dummy_data = np.random.randn(1000, 100)
    
    def dummy_process_fn(batch):
        return torch.matmul(batch, batch.T)
    
    results = batch_processor.process_in_batches(dummy_data, dummy_process_fn)
    print(f"Batch processing result shape: {results.shape}")
    
    print("GPU acceleration test complete!")
