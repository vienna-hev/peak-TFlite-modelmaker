# TFLite Model Maker stack (Python 3.9, TF 2.8.0, TFLMM 0.4.2)
FROM python:3.9-slim

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONNOUSERSITE=1 \
    TF_CPP_MIN_LOG_LEVEL=2

# System deps (audio/media + build). libportaudio2 requested; libsndfile1 for librosa/soundfile; ffmpeg for media.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl ca-certificates \
    libsndfile1 libportaudio2 ffmpeg \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY requirements.txt /workspace/requirements.txt

# Install heavy/picky wheels FIRST to avoid resolver backtracking and keep TF pinned
# - numpy is constrained by your req file (<1.23.4). Use 1.23.3 to keep np.object compatibility.
# - tensorflow==2.8.0 as requested
# - opencv-python-headless==4.1.2.30 (from your command list)
# - pycocotools (you asked to include it explicitly)
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install --no-cache-dir --prefer-binary \
        numpy==1.23.3 \
        tensorflow==2.8.0 \
        opencv-python-headless==4.5.5.64 \
        pycocotools==2.0.7 && \
    python -m pip install --no-cache-dir --prefer-binary -r /workspace/requirements.txt && \
    python -m pip install --no-cache-dir --prefer-binary --no-deps tflite-model-maker==0.4.2


# Optional: the source install path you listed; keep it commented so it's "included" but not executed.
# If you ever need to install from source instead of PyPI, uncomment this block:
# RUN git clone https://github.com/tensorflow/examples /tmp/examples && \
#     cd /tmp/examples/tensorflow_examples/lite/model_maker/pip_package && \
#     python -m pip install -e .

# Safer non-root default user
RUN useradd -m developer
USER developer
WORKDIR /workspace

# Default entrypoint: just give you a shell; you can run jupyter or scripts as you like.
CMD ["bash"]
