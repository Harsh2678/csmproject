import importlib.metadata

try:
    print("Razorpay version:", importlib.metadata.version("razorpay"))
except importlib.metadata.PackageNotFoundError:
    print("Razorpay is not installed")