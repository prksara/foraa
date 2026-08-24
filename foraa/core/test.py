import torch
print("FORAA AI SYSTEM")
print("================")
print("PyTorch:", torch.__version__)
17
print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
 print("GPU:", torch.cuda.get_device_name(0))
else:
 print("Running in CPU mode.")
