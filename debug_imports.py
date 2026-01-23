import sys
print(f"Python Version: {sys.version}")

try:
    import numpy
    print(f"Numpy Version: {numpy.__version__}")
    print(f"Numpy Path: {numpy.__file__}")
except ImportError as e:
    print(f"Numpy Import Error: {e}")

try:
    import cv2
    print(f"OpenCV Version: {cv2.__version__}")
except ImportError as e:
    print(f"OpenCV Import Error: {e}")
    import traceback
    traceback.print_exc()

try:
    import tensorflow
    print(f"TensorFlow Version: {tensorflow.__version__}")
except ImportError as e:
    print(f"TensorFlow Import Error: {e}")
