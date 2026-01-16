"""
YOLO Model Benchmarking for Jetson Orin Nano
Tests PyTorch baseline and TensorRT optimization.

Usage:
    python3 benchmark_models.py --step all          # Complete pipeline
    python3 benchmark_models.py --step pytorch      # PyTorch only
    python3 benchmark_models.py --step export       # Export to TensorRT
    python3 benchmark_models.py --step tensorrt     # TensorRT only
    python3 benchmark_models.py --step compare      # Analysis only
"""

import argparse
import time
import pandas as pd
from pathlib import Path
from ultralytics import YOLO


class ModelBenchmark:
    """Benchmark individual YOLO model."""
    
    def __init__(self, model_path, backend, test_image, classes, num_runs=10):
        self.model_path = model_path
        self.backend = backend
        self.test_image = test_image
        self.classes = classes
        self.num_runs = num_runs
        self.model_name = Path(model_path).stem
    
    def run(self):
        """Run benchmark and return results."""
        print(f"[TEST] {self.model_name} ({self.backend})")
        
        try:
            model = self._load_model()
            self._warmup(model)
            times = self._benchmark_runs(model)
            return self._calculate_results(times)
        except Exception as e:
            print(f"  [ERROR] {e}")
            return None
    
    def _load_model(self):
        """Load YOLO model."""
        return YOLO(f'models/{self.model_path}')
    
    def _warmup(self, model):
        """Perform warm-up inference."""
        _ = model(self.test_image, classes=self.classes, verbose=False)
    
    def _benchmark_runs(self, model):
        """Run multiple inferences and time them."""
        times = []
        for _ in range(self.num_runs):
            start = time.time()
            _ = model(self.test_image, classes=self.classes, verbose=False)
            times.append((time.time() - start) * 1000)
        return times
    
    def _calculate_results(self, times):
        """Calculate benchmark statistics."""
        avg_time = sum(times) / len(times)
        fps = 1000 / avg_time
        
        print(f"  {avg_time:.2f}ms | {fps:.1f} FPS")
        
        return {
            'model': self.model_name,
            'version': 'v5' if 'yolov5' in self.model_name else 'v11',
            'size': self.model_name[-1],
            'inference_time_ms': round(avg_time, 2),
            'fps': round(fps, 1),
            'backend': self.backend
        }


class BenchmarkPipeline:
    """Complete benchmarking pipeline for Jetson Orin Nano."""
    
    def __init__(self):
        self.test_image = 'testimages/test_image3.jpg'
        self.classes = [0]  # person
        self.num_runs = 10
        self.models = [
            'yolov5n.pt', 'yolov5s.pt', 'yolov5m.pt',
            'yolo11n.pt', 'yolo11s.pt', 'yolo11m.pt'
        ]
        Path('results').mkdir(exist_ok=True)
    
    def run_pytorch(self):
        """Phase 1: PyTorch baseline benchmarking."""
        print("\n" + "=" * 70)
        print("PHASE 1: PyTorch Baseline")
        print("=" * 70 + "\n")
        
        results = []
        for model_path in self.models:
            benchmark = ModelBenchmark(
                model_path, 'pytorch', self.test_image, self.classes, self.num_runs
            )
            result = benchmark.run()
            if result:
                results.append(result)
        
        self._save_results(results, 'orin_pytorch_results.csv')
        return results
    
    def run_export(self):
        """Phase 2: Export to TensorRT."""
        print("\n" + "=" * 70)
        print("PHASE 2: TensorRT Export")
        print("=" * 70)
        print("Note: ~5-10 min per model (~60 min total)\n")
        
        for model_path in self.models:
            model_name = Path(model_path).stem
            engine_path = Path('models') / f"{model_name}.engine"
            
            if engine_path.exists():
                print(f"[EXISTS] {model_name}.engine")
                continue
            
            print(f"[EXPORT] {model_name} -> TensorRT")
            
            try:
                model = YOLO(f'models/{model_path}')
                model.export(format='engine', half=True, device=0)
                print(f"  Exported")
            except Exception as e:
                print(f"  Error: {e}")
        
        print("\nTensorRT export complete")
    
    def run_tensorrt(self):
        """Phase 3: TensorRT benchmarking."""
        print("\n" + "=" * 70)
        print("PHASE 3: TensorRT Benchmarking")
        print("=" * 70 + "\n")
        
        results = []
        for model_path in self.models:
            model_name = Path(model_path).stem
            engine_path = f'{model_name}.engine'
            
            if not Path(f'models/{engine_path}').exists():
                print(f"[SKIP] {model_name}.engine (not found)")
                continue
            
            benchmark = ModelBenchmark(
                engine_path, 'tensorrt', self.test_image, self.classes, self.num_runs
            )
            result = benchmark.run()
            if result:
                results.append(result)
        
        self._save_results(results, 'orin_tensorrt_results.csv')
        return results
    
    def run_comparison(self):
        """Phase 4: Generate comprehensive analysis."""
        print("\n" + "=" * 70)
        print("PHASE 4: Analysis & Comparison")
        print("=" * 70 + "\n")
        
        analyzer = ResultsAnalyzer()
        analyzer.run()
    
    def _save_results(self, results, filename):
        """Save results to CSV."""
        if not results:
            print("[ERROR] No results to save")
            return
        
        df = pd.DataFrame(results)
        output_path = Path('results') / filename
        df.to_csv(output_path, index=False)
        print(f"\n Saved to {output_path}")


class ResultsAnalyzer:
    """Analyze and compare benchmark results."""
    
    def __init__(self):
        self.results_dir = Path('results')
    
    def run(self):
        """Run complete analysis."""
        df_all = self._load_all_results()
        
        if df_all is None:
            print("[ERROR] No results to analyze")
            return
        
        self._save_combined(df_all)
        self._print_model_evolution(df_all)
        self._print_tensorrt_speedup(df_all)
        self._print_device_comparison(df_all)
        self._save_recommendation(df_all)
    
    def _load_all_results(self):
        """Load all CSV results."""
        dfs = []
        
        # Load Jetson results
        pytorch_file = self.results_dir / 'orin_pytorch_results.csv'
        tensorrt_file = self.results_dir / 'orin_tensorrt_results.csv'
        
        if pytorch_file.exists():
            df = pd.read_csv(pytorch_file)
            df['device'] = 'jetson_orin'
            dfs.append(df)
        
        if tensorrt_file.exists():
            df = pd.read_csv(tensorrt_file)
            df['device'] = 'jetson_orin'
            dfs.append(df)
        
        # Load laptop baseline (optional)
        laptop_file = self.results_dir / 'laptop_baseline_results.csv'
        if laptop_file.exists():
            df = pd.read_csv(laptop_file)
            dfs.append(df)
            print("[INFO] Including laptop baseline\n")
        
        return pd.concat(dfs, ignore_index=True) if dfs else None
    
    def _save_combined(self, df):
        """Save combined results."""
        output_file = self.results_dir / 'complete_comparison.csv'
        df.to_csv(output_file, index=False)
        print(f"Saved to {output_file}\n")
    
    def _print_model_evolution(self, df):
        """Print YOLOv5 vs YOLOv11 comparison."""
        print("=" * 70)
        print("MODEL EVOLUTION (YOLOv5 vs YOLOv11)")
        print("=" * 70)
        
        jetson = df[df['device'] == 'jetson_orin']
        
        for backend in ['pytorch', 'tensorrt']:
            print(f"\n{backend.upper()}:")
            for size in ['n', 's', 'm']:
                v5 = jetson[(jetson['version'] == 'v5') & 
                           (jetson['size'] == size) & 
                           (jetson['backend'] == backend)]
                v11 = jetson[(jetson['version'] == 'v11') & 
                            (jetson['size'] == size) & 
                            (jetson['backend'] == backend)]
                
                if not v5.empty and not v11.empty:
                    v5_fps = v5['fps'].values[0]
                    v11_fps = v11['fps'].values[0]
                    improvement = ((v11_fps - v5_fps) / v5_fps) * 100
                    print(f"  Size {size}: YOLOv5 {v5_fps:.1f} FPS -> "
                          f"YOLOv11 {v11_fps:.1f} FPS ({improvement:+.1f}%)")
        print()
    
    def _print_tensorrt_speedup(self, df):
        """Print TensorRT optimization speedup."""
        print("=" * 70)
        print("TENSORRT SPEEDUP")
        print("=" * 70 + "\n")
        
        jetson = df[df['device'] == 'jetson_orin']
        
        for model in jetson['model'].unique():
            pytorch = jetson[(jetson['model'] == model) & (jetson['backend'] == 'pytorch')]
            tensorrt = jetson[(jetson['model'] == model) & (jetson['backend'] == 'tensorrt')]
            
            if not pytorch.empty and not tensorrt.empty:
                pytorch_fps = pytorch['fps'].values[0]
                tensorrt_fps = tensorrt['fps'].values[0]
                speedup = tensorrt_fps / pytorch_fps
                print(f"{model}: {pytorch_fps:.1f} FPS -> {tensorrt_fps:.1f} FPS "
                      f"({speedup:.2f}x speedup)")
        print()
    
    def _print_device_comparison(self, df):
        """Compare laptop vs Jetson performance."""
        if 'laptop' not in df['device'].values:
            return
        
        print("=" * 70)
        print("DEVICE COMPARISON (Laptop vs Jetson)")
        print("=" * 70 + "\n")
        
        for model in ['yolov5s', 'yolo11s']:
            laptop = df[(df['model'] == model) & (df['device'] == 'laptop')]
            jetson_pyt = df[(df['model'] == model) & (df['device'] == 'jetson_orin') & 
                           (df['backend'] == 'pytorch')]
            jetson_trt = df[(df['model'] == model) & (df['device'] == 'jetson_orin') & 
                           (df['backend'] == 'tensorrt')]
            
            if not laptop.empty and not jetson_pyt.empty:
                print(f"{model}:")
                laptop_fps = laptop['fps'].values[0]
                jetson_pyt_fps = jetson_pyt['fps'].values[0]
                print(f"  Laptop (PyTorch):  {laptop_fps:.1f} FPS")
                print(f"  Jetson (PyTorch):  {jetson_pyt_fps:.1f} FPS "
                      f"({jetson_pyt_fps/laptop_fps*100:.0f}%)")
                
                if not jetson_trt.empty:
                    jetson_trt_fps = jetson_trt['fps'].values[0]
                    print(f"  Jetson (TensorRT): {jetson_trt_fps:.1f} FPS "
                          f"({jetson_trt_fps/laptop_fps*100:.0f}%)")
                print()
        print()
    
    def _save_recommendation(self, df):
        """Save model selection recommendation."""
        best = df[(df['model'] == 'yolo11s') & 
                 (df['device'] == 'jetson_orin') & 
                 (df['backend'] == 'tensorrt')]
        
        if best.empty:
            return
        
        fps = best['fps'].values[0]
        
        print("=" * 70)
        print("MODEL SELECTION RECOMMENDATION")
        print("=" * 70 + "\n")
        
        recommendation = f"""SELECTED MODEL: YOLOv11s with TensorRT

Performance: {fps:.1f} FPS on Jetson Orin Nano
Real-time capable: {'YES' if fps > 30 else 'NO'} (30+ FPS threshold)
"""
        
        print(recommendation)
        
        # Save to file
        output_file = self.results_dir / 'model_selection.txt'
        with open(output_file, 'w') as f:
            f.write(recommendation)
        
        print(f"Saved to {output_file}")
        print("\n" + "=" * 70)
        print("ANALYSIS COMPLETE")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='YOLO Benchmarking Pipeline')
    parser.add_argument('--step', 
                       choices=['all', 'pytorch', 'export', 'tensorrt', 'compare'],
                       default='all',
                       help='Which step to run')
    args = parser.parse_args()
    
    pipeline = BenchmarkPipeline()
    
    if args.step in ['all', 'pytorch']:
        pipeline.run_pytorch()
    
    if args.step in ['all', 'export']:
        pipeline.run_export()
    
    if args.step in ['all', 'tensorrt']:
        pipeline.run_tensorrt()
    
    if args.step in ['all', 'compare']:
        pipeline.run_comparison()
    
    print("\nBENCHMARKING COMPLETE")


if __name__ == '__main__':
    main()
