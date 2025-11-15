#!/usr/bin/env python3
"""
train.py

TFLite Model Maker object detection training script.
Trains an object detection model on your dataset and exports a TFLite model.

Usage:
    python train.py [--help] [--epochs 100] [--batch-size 32] [--output model.tflite]
"""

import os
import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Train TFLite object detection model using Model Maker"
    )
    parser.add_argument(
        "--images",
        default="/workspace/data/images",
        help="Path to images directory (Pascal VOC format)"
    )
    parser.add_argument(
        "--annotations",
        default="/workspace/data/annotations",
        help="Path to annotations directory (Pascal VOC XML)"
    )
    parser.add_argument(
        "--output",
        default="/workspace/exported_model/model.tflite",
        help="Path to output TFLite model"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Number of training epochs (default: 100)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for training (default: 32)"
    )
    parser.add_argument(
        "--export-dir",
        default="/workspace/exported_model",
        help="Directory to export model and metadata"
    )
    
    args = parser.parse_args()

    # Validate inputs
    if not os.path.isdir(args.images):
        print(f"[ERROR] Images directory not found: {args.images}")
        sys.exit(1)
    if not os.path.isdir(args.annotations):
        print(f"[ERROR] Annotations directory not found: {args.annotations}")
        sys.exit(1)

    # Create export directory if needed
    os.makedirs(args.export_dir, exist_ok=True)

    print("=" * 70)
    print("TFLite Model Maker - Object Detection Training")
    print("=" * 70)
    print(f"Images directory:      {args.images}")
    print(f"Annotations directory: {args.annotations}")
    print(f"Export directory:      {args.export_dir}")
    print(f"Output model:          {args.output}")
    print(f"Epochs:                {args.epochs}")
    print(f"Batch size:            {args.batch_size}")
    print("=" * 70)

    try:
        from tflite_model_maker import object_detector
    except ImportError as e:
        print(f"[ERROR] Failed to import tflite_model_maker: {e}")
        print("Make sure the environment has tflite_model_maker installed.")
        sys.exit(1)

    print("\n[1/4] Loading dataset from Pascal VOC annotations...")
    try:
        train_data = object_detector.DataLoader.from_pascal_voc(
            args.images,
            args.annotations,
            ['testlabel']  # Replace with your actual labels
        )
        print(f"[OK] Dataset loaded: {len(train_data)} examples")
    except Exception as e:
        print(f"[ERROR] Failed to load dataset: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("  - Check that image filenames match XML annotation filenames")
        print("  - Ensure XML files are valid Pascal VOC format")
        print("  - Verify XML files contain <object> and <bndbox> elements")
        sys.exit(1)

    print("\n[2/4] Creating model specification...")
    try:
        spec = object_detector.EfficientDetLite0Spec()
        print("[OK] Using EfficientDet-Lite0 model spec")
    except Exception as e:
        print(f"[ERROR] Failed to load model spec: {e}")
        sys.exit(1)

    print("\n[3/4] Training object detection model...")
    print("This may take several minutes depending on dataset size and hardware...")
    try:
        model = object_detector.create(
            train_data,
            model_spec=spec,
            epochs=args.epochs,
            batch_size=args.batch_size,
            train_whole_model=False
        )
        print("[OK] Training completed successfully")
    except Exception as e:
        print(f"[ERROR] Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n[4/4] Exporting TFLite model...")
    try:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        model.export(export_dir=args.export_dir, tflite_filename='model.tflite')
        print(f"[OK] Model exported to: {args.output}")
        print(f"[OK] Metadata exported to: {args.export_dir}/model_metadata.json")
    except Exception as e:
        print(f"[ERROR] Export failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 70)
    print("Training completed successfully!")
    print(f"Model location: {os.path.abspath(args.output)}")
    print("=" * 70)

if __name__ == "__main__":
    main()
