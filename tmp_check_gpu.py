import torch
import tensorflow as tf
import cv2

print("--- GPU Diagnostic ---")

# Check PyTorch (used by YOLOv8)
print(f"PyTorch version: {torch.__version__}")
cuda_available = torch.cuda.is_available()
print(f"PyTorch CUDA available: {cuda_available}")
if cuda_available:
    print(f"PyTorch Device Name: {torch.cuda.get_device_name(0)}")
    print(f"PyTorch Device Count: {torch.cuda.device_count()}")

print("-" * 20)

# Check TensorFlow (used by MoveNet)
print(f"TensorFlow version: {tf.__version__}")
gpu_devices = tf.config.list_physical_devices('GPU')
print(f"TensorFlow GPU devices found: {len(gpu_devices)}")
for gpu in gpu_devices:
    print(f" - {gpu}")

print("-" * 20)

# Check OpenCV (optional, but good to know)
print(f"OpenCV version: {cv2.__version__}")
print(f"OpenCV Build Information (CUDA): {'WITH_CUDA' in cv2.getBuildInformation()}")
