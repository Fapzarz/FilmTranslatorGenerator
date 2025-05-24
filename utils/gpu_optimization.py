"""
Advanced GPU Optimization utilities for Film Translator Generator
Provides enhanced GPU acceleration and performance monitoring
"""
import torch
import gc
import psutil
import time
import nvidia_ml_py3 as nvml
from typing import Dict, Optional, Tuple, List

class GPUOptimizer:
    """Advanced GPU optimization and monitoring"""
    
    def __init__(self):
        self.gpu_available = torch.cuda.is_available()
        self.gpu_initialized = False
        self.gpu_info = {}
        self.memory_stats = {}
        
        if self.gpu_available:
            self._initialize_gpu_monitoring()
    
    def _initialize_gpu_monitoring(self):
        """Initialize GPU monitoring with nvidia-ml-py"""
        try:
            nvml.nvmlInit()
            self.gpu_initialized = True
            self._collect_gpu_info()
        except Exception as e:
            print(f"GPU monitoring initialization failed: {e}")
            self.gpu_initialized = False
    
    def _collect_gpu_info(self):
        """Collect detailed GPU information"""
        if not self.gpu_initialized:
            return
        
        try:
            device_count = nvml.nvmlDeviceGetCount()
            self.gpu_info = {}
            
            for i in range(device_count):
                handle = nvml.nvmlDeviceGetHandleByIndex(i)
                
                # Basic info
                name = nvml.nvmlDeviceGetName(handle).decode('utf-8')
                memory_info = nvml.nvmlDeviceGetMemoryInfo(handle)
                
                # Performance info
                try:
                    power_usage = nvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                    power_limit = nvml.nvmlDeviceGetPowerManagementLimitConstraints(handle)[1] / 1000.0
                except:
                    power_usage = power_limit = None
                
                try:
                    temp = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
                except:
                    temp = None
                
                # Compute capability
                major, minor = nvml.nvmlDeviceGetCudaComputeCapability(handle)
                
                self.gpu_info[i] = {
                    'name': name,
                    'memory_total': memory_info.total,
                    'memory_free': memory_info.free,
                    'memory_used': memory_info.used,
                    'power_usage': power_usage,
                    'power_limit': power_limit,
                    'temperature': temp,
                    'compute_capability': f"{major}.{minor}",
                    'handle': handle
                }
        except Exception as e:
            print(f"Error collecting GPU info: {e}")
    
    def get_optimal_device_settings(self) -> Dict[str, str]:
        """Determine optimal device and compute type settings"""
        if not self.gpu_available:
            return {'device': 'cpu', 'compute_type': 'int8'}
        
        self._collect_gpu_info()
        
        # Get primary GPU info
        if 0 in self.gpu_info:
            gpu = self.gpu_info[0]
            total_memory_gb = gpu['memory_total'] / (1024**3)
            free_memory_gb = gpu['memory_free'] / (1024**3)
            compute_cap = float(gpu['compute_capability'])
            
            # Determine optimal compute type based on memory and capability
            if total_memory_gb >= 8 and free_memory_gb >= 4 and compute_cap >= 7.5:
                compute_type = 'float16'  # Best quality
            elif total_memory_gb >= 6 and free_memory_gb >= 3:
                compute_type = 'int8_float16'  # Balanced
            elif free_memory_gb >= 2:
                compute_type = 'int8'  # Memory efficient
            else:
                return {'device': 'cpu', 'compute_type': 'int8'}  # Fall back to CPU
            
            return {'device': 'cuda', 'compute_type': compute_type}
        
        return {'device': 'cuda', 'compute_type': 'int8'}
    
    def optimize_memory(self, aggressive: bool = False):
        """Optimize GPU memory usage"""
        if not self.gpu_available:
            return
        
        # Clear PyTorch cache
        torch.cuda.empty_cache()
        
        if aggressive:
            # Force garbage collection
            gc.collect()
            
            # Clear all GPU memory
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
            
            # Additional memory cleanup
            if hasattr(torch.cuda, 'reset_accumulated_memory_stats'):
                torch.cuda.reset_accumulated_memory_stats()
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current GPU memory usage in GB"""
        if not self.gpu_available:
            return {}
        
        self._collect_gpu_info()
        memory_stats = {}
        
        for gpu_id, info in self.gpu_info.items():
            memory_stats[f'gpu_{gpu_id}'] = {
                'total_gb': info['memory_total'] / (1024**3),
                'used_gb': info['memory_used'] / (1024**3),
                'free_gb': info['memory_free'] / (1024**3),
                'usage_percent': (info['memory_used'] / info['memory_total']) * 100
            }
        
        return memory_stats
    
    def get_performance_stats(self) -> Dict[str, any]:
        """Get comprehensive performance statistics"""
        stats = {
            'gpu_available': self.gpu_available,
            'gpu_count': len(self.gpu_info) if self.gpu_info else 0,
            'cpu_usage': psutil.cpu_percent(interval=1),
            'ram_usage': psutil.virtual_memory().percent,
            'ram_available_gb': psutil.virtual_memory().available / (1024**3)
        }
        
        if self.gpu_available and self.gpu_info:
            stats['gpu_stats'] = {}
            for gpu_id, info in self.gpu_info.items():
                stats['gpu_stats'][f'gpu_{gpu_id}'] = {
                    'name': info['name'],
                    'memory_usage_percent': (info['memory_used'] / info['memory_total']) * 100,
                    'temperature': info['temperature'],
                    'power_usage': info['power_usage'],
                    'compute_capability': info['compute_capability']
                }
        
        return stats
    
    def suggest_batch_size(self, model_size: str = "large-v2") -> int:
        """Suggest optimal batch size based on available memory"""
        memory_stats = self.get_memory_usage()
        
        if not memory_stats:
            return 500  # Default for CPU
        
        primary_gpu = next(iter(memory_stats.values()))
        free_memory_gb = primary_gpu['free_gb']
        
        # Batch size recommendations based on model size and available memory
        batch_recommendations = {
            'tiny': {'low': 1000, 'med': 2000, 'high': 4000},
            'base': {'low': 800, 'med': 1500, 'high': 3000},
            'small': {'low': 600, 'med': 1200, 'high': 2500},
            'medium': {'low': 400, 'med': 800, 'high': 1500},
            'large-v2': {'low': 200, 'med': 500, 'high': 1000},
            'large-v3': {'low': 200, 'med': 500, 'high': 1000}
        }
        
        model_key = model_size if model_size in batch_recommendations else 'large-v2'
        recommendations = batch_recommendations[model_key]
        
        if free_memory_gb >= 6:
            return recommendations['high']
        elif free_memory_gb >= 4:
            return recommendations['med']
        else:
            return recommendations['low']
    
    def monitor_processing(self, interval: float = 2.0) -> Dict[str, any]:
        """Monitor system during processing"""
        if not self.gpu_available:
            return {}
        
        # Take snapshot before processing starts
        initial_stats = self.get_performance_stats()
        
        return {
            'timestamp': time.time(),
            'stats': initial_stats,
            'memory_usage': self.get_memory_usage()
        }
    
    def cleanup(self):
        """Cleanup GPU resources"""
        self.optimize_memory(aggressive=True)
        
        if self.gpu_initialized:
            try:
                nvml.nvmlShutdown()
            except:
                pass


class PerformanceMonitor:
    """Monitor and log performance metrics during processing"""
    
    def __init__(self):
        self.gpu_optimizer = GPUOptimizer()
        self.processing_stats = []
        self.start_time = None
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        initial_stats = self.gpu_optimizer.monitor_processing()
        self.processing_stats = [initial_stats]
        return initial_stats
    
    def log_checkpoint(self, stage: str):
        """Log performance at a specific processing stage"""
        if self.start_time is None:
            return
        
        current_stats = self.gpu_optimizer.monitor_processing()
        current_stats['stage'] = stage
        current_stats['elapsed_time'] = time.time() - self.start_time
        
        self.processing_stats.append(current_stats)
        return current_stats
    
    def get_performance_report(self) -> Dict[str, any]:
        """Generate comprehensive performance report"""
        if not self.processing_stats:
            return {}
        
        total_time = time.time() - self.start_time if self.start_time else 0
        
        report = {
            'total_processing_time': total_time,
            'gpu_available': self.gpu_optimizer.gpu_available,
            'optimization_suggestions': self._generate_suggestions(),
            'performance_timeline': self.processing_stats
        }
        
        return report
    
    def _generate_suggestions(self) -> List[str]:
        """Generate optimization suggestions based on monitoring data"""
        suggestions = []
        
        if not self.processing_stats:
            return suggestions
        
        latest_stats = self.processing_stats[-1]
        
        # Memory usage suggestions
        if 'memory_usage' in latest_stats:
            for gpu_id, mem_stats in latest_stats['memory_usage'].items():
                if mem_stats['usage_percent'] > 90:
                    suggestions.append(f"GPU memory usage high ({mem_stats['usage_percent']:.1f}%) - consider smaller batch size or int8 compute type")
                elif mem_stats['usage_percent'] < 50:
                    suggestions.append(f"GPU memory underutilized ({mem_stats['usage_percent']:.1f}%) - consider larger batch size for better performance")
        
        # CPU/RAM suggestions
        if 'stats' in latest_stats:
            cpu_usage = latest_stats['stats'].get('cpu_usage', 0)
            ram_usage = latest_stats['stats'].get('ram_usage', 0)
            
            if cpu_usage > 90:
                suggestions.append("CPU usage very high - consider reducing concurrent processes")
            
            if ram_usage > 90:
                suggestions.append("RAM usage critical - consider smaller batch sizes or closing other applications")
        
        return suggestions 