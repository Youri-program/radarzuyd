"""
Laptop Baseline Benchmarking
Measures desktop performance as reference baseline.
"""

from ultralytics import YOLO
import time
import pandas as pd
import platform
from pathlib import Path


class LaptopBenchmark:
    """Benchmark YOLO models on laptop for baseline reference."""
    
    def __init__(self):
        self.test_image = 'testimages/test_image3.jpg'
        self.classes = [0]  # person
        self.num_runs = 10
        self.models = [
            'yolov5n.pt', 'yolov5s.pt', 'yolov5m.pt',
            'yolo11n.pt', 'yolo11s.pt', 'yolo11m.pt'
        ]
        self.results = []
        Path('results').mkdir(exist_ok=True)
    
    def run(self):
        """Run complete benchmark pipeline."""
        self._print_header()
        self._benchmark_all_models()
        self._save_results()
        self._print_comparison()
    
    def _print_header(self):
        """Print benchmark header."""
        print("=" * 70)
        print("LAPTOP BASELINE BENCHMARKING")
        print("=" * 70)
        print(f"Platform: {platform.platform()}")
        print(f"Test Image: {self.test_image}")
        print(f"Runs per model: {self.num_runs}")
        print()
    
    def _benchmark_all_models(self):
        """Benchmark all models."""
        for model_path in self.models:
            result = self._benchmark_single_model(model_path)
            if result:
                self.results.append(result)
    
    def _benchmark_single_model(self, model_path):
        """Benchmark a single model."""
        model_name = model_path.replace('.pt', '')
        print(f"[TEST] {model_name}")
        
        try:
            # Load model
            model = YOLO(f'models/{model_path}')
            
            # Warm-up
            _ = model(self.test_image, classes=self.classes, verbose=False)
            
            # Benchmark runs
            times = []
            for _ in range(self.num_runs):
                start = time.time()
                result = model(self.test_image, classes=self.classes, verbose=False)
                times.append((time.time() - start) * 1000)
            
            # Calculate stats
            avg_time = sum(times) / len(times)
            fps = 1000 / avg_time
            
            print(f"  {avg_time:.2f}ms | {fps:.1f} FPS")
            
            return {
                'model': model_name,
                'version': 'v5' if 'yolov5' in model_name else 'v11',
                'size': model_name[-1],
                'inference_time_ms': round(avg_time, 2),
                'fps': round(fps, 1),
                'device': 'laptop',
                'backend': 'pytorch'
            }
        except Exception as e:
            print(f"  [ERROR] {e}")
            return None
    
    def _save_results(self):
        """Save results to CSV."""
        df = pd.DataFrame(self.results)
        df.to_csv('results/laptop_baseline_results.csv', index=False)
        
        print()
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(df.to_string(index=False))
        print()
    
    def _print_comparison(self):
        """Print YOLOv5 vs YOLOv11 comparison."""
        df = pd.DataFrame(self.results)
        
        print("YOLOv5 vs YOLOv11 Comparison:")
        print("-" * 70)
        for size in ['n', 's', 'm']:
            v5 = df[(df['version'] == 'v5') & (df['size'] == size)]['fps'].values[0]
            v11 = df[(df['version'] == 'v11') & (df['size'] == size)]['fps'].values[0]
            improvement = ((v11 - v5) / v5) * 100
            print(f"  Size {size}: {v5:.1f} FPS → {v11:.1f} FPS (+{improvement:.1f}%)")
        print("-" * 70)
        print()
        print("Saved to results/laptop_baseline_results.csv")


if __name__ == '__main__':
    benchmark = LaptopBenchmark()
    benchmark.run()
