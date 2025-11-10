# TFLite Model Maker Training Project

This project uses **TensorFlow Lite Model Maker** to train object detection models using the Pascal VOC dataset format.

## Project Structure

```
take68/
├── Dockerfile                 # Container definition (TF 2.8.0, TFLMM 0.4.2)
├── docker-compose.yml         # Docker Compose configuration
├── requirements.txt           # Python dependencies (pinned versions)
├── build-and-run.ps1         # Setup script for Windows PowerShell
├── README.md                  # This file
└── workspace/
    ├── train.py              # Main training script
    ├── check-training-env.py  # Environment validation script
    ├── data/
    │   ├── images/           # Your training images (JPG/PNG)
    │   └── annotations/      # Pascal VOC XML annotations
    └── exported_model/       # Output directory for trained models
```

## Prerequisites

1. **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop)
   - Windows: Docker Desktop for Windows with WSL 2 backend recommended
   - At least 8GB RAM allocated to Docker
   - At least 5GB free disk space for the base image

2. **Dataset Preparation**
   - Create training images in `workspace/data/images/` (JPG, PNG, BMP)
   - Create Pascal VOC annotations in `workspace/data/annotations/` (XML files)
   - Image and XML files must have matching basenames (e.g., `image_001.jpg` ↔ `image_001.xml`)

## Quick Start

### Step 1: Prepare Your Dataset

1. Place your training images in:
   ```
   workspace/data/images/
   ```

2. Create Pascal VOC XML annotations in:
   ```
   workspace/data/annotations/
   ```

   **XML Format Example:**
   ```xml
   <annotation>
     <filename>image_001.jpg</filename>
     <size>
       <width>640</width>
       <height>480</height>
       <depth>3</depth>
     </size>
     <object>
       <name>cat</name>
       <bndbox>
         <xmin>50</xmin>
         <ymin>100</ymin>
         <xmax>150</xmax>
         <ymax>200</ymax>
       </bndbox>
     </object>
   </annotation>
   ```

### Step 2: Build and Check Environment

Open PowerShell in the `take68` directory and run:

```powershell
.\build-and-run.ps1
```

This will:
1. Build the Docker image
2. Run the environment check to verify everything is ready
3. Show you what the next steps are

### Step 3: Train Your Model

Once the environment check passes, train your model:

```powershell
docker-compose run --rm tflmm python /workspace/train.py
```

**Optional training parameters:**
```powershell
docker-compose run --rm tflmm python /workspace/train.py `
    --epochs 200 `
    --batch-size 16 `
    --images /workspace/data/images `
    --annotations /workspace/data/annotations `
    --output /workspace/exported_model/model.tflite
```

### Step 4: Find Your Model

The trained model will be exported to:
```
workspace/exported_model/model.tflite
workspace/exported_model/model_metadata.json
```

## Troubleshooting

### "Docker is not installed"
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
- Restart your computer after installation

### "No matching image/annotation basenames found"
- Ensure your image and XML files have identical names (except extension)
- Example: `photo_001.jpg` must have a corresponding `photo_001.xml`

### "Cannot import tflite_model_maker"
- Run `.\build-and-run.ps1` first to build the Docker image
- This script automatically installs all dependencies in the container

### "Low disk space" warning
- Ensure you have at least 5GB free disk space
- Model Maker creates intermediate files during training

### "Python 3.9+ required"
- The Docker image automatically uses Python 3.9
- No action needed if using Docker

## Advanced Usage

### Run a Shell in the Container

```powershell
docker-compose run --rm tflmm bash
```

Then you can run Python interactively or run custom commands.

### Customize Training Parameters

Edit `workspace/train.py` or use command-line arguments:

```powershell
docker-compose run --rm tflmm python /workspace/train.py `
    --epochs 500 `
    --batch-size 8
```

### View Logs

If training encounters an error, the full traceback will be printed. Save it for debugging:

```powershell
docker-compose run --rm tflmm python /workspace/train.py 2>&1 | Tee-Object -FilePath training.log
```

## Dataset Format Requirements

### Images
- Supported formats: JPG, JPEG, PNG, BMP
- Recommended size: 640×480 or larger
- Minimum recommended: 50+ images per class
- Minimum for training: 10+ images total

### Annotations (Pascal VOC XML)
Required elements:
- `<filename>`: Matching image filename
- `<size>`: Image dimensions (width, height, depth)
- `<object>`: One or more objects with:
  - `<name>`: Class label (e.g., "cat", "dog")
  - `<bndbox>`: Bounding box with xmin, ymin, xmax, ymax

## Model Specifications

This project uses **EfficientDet-Lite0** as the default model architecture:
- Lightweight (8-10MB TFLite model)
- Good accuracy/speed tradeoff
- Suitable for edge devices (mobile, embedded)
- Training typically takes 5-30 minutes on CPU

## What Each Script Does

| Script | Purpose |
|--------|---------|
| `Dockerfile` | Defines the Docker container with TF 2.8.0 and dependencies |
| `docker-compose.yml` | Orchestrates the container and volume mounts |
| `build-and-run.ps1` | Windows setup script to build image and verify environment |
| `train.py` | Main training script using TFLite Model Maker API |
| `check-training-env.py` | Validates all dependencies, Python version, and dataset format |

## Performance Tips

1. **Use GPU if available**: Docker will auto-detect NVIDIA GPUs. Install [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-docker) for GPU support.

2. **Increase batch size** (if not running out of memory):
   ```powershell
   docker-compose run --rm tflmm python /workspace/train.py --batch-size 64
   ```

3. **Add more training data**: Collect 100-500+ images per class for best results.

4. **Longer training**: Increase epochs for more accuracy:
   ```powershell
   docker-compose run --rm tflmm python /workspace/train.py --epochs 500
   ```

## Model Export

After successful training, your model is in:
- **model.tflite** - Quantized TFLite model for deployment
- **model_metadata.json** - Class labels and input/output specs

Use these in your mobile/embedded applications.

## License

This project uses:
- TensorFlow Lite (Apache 2.0)
- TensorFlow Model Maker (Apache 2.0)
- Other dependencies listed in `requirements.txt`

## Support

For issues:
1. Run `.\build-and-run.ps1` to verify the environment
2. Check dataset format with `docker-compose run --rm tflmm python /workspace/check-training-env.py`
3. Review TensorFlow documentation: https://www.tensorflow.org/lite/guide/model_maker

---

**Happy training!** 🚀
