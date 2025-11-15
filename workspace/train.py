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
        default="/workspace/data/images/train",
        help="Path to training images directory (Pascal VOC format)"
    )
    parser.add_argument(
        "--annotations",
        default="/workspace/data/annotations/train",
        help="Path to training annotations directory (Pascal VOC XML)"
    )
    parser.add_argument(
        "--val-images",
        default="/workspace/data/images/valid",
        help="Path to validation images directory"
    )
    parser.add_argument(
        "--val-annotations",
        default="/workspace/data/annotations/valid",
        help="Path to validation annotations directory"
    )
    parser.add_argument(
        "--test-images",
        default="/workspace/data/images/test",
        help="Path to test images directory"
    )
    parser.add_argument(
        "--test-annotations",
        default="/workspace/data/annotations/test",
        help="Path to test annotations directory"
    )
    parser.add_argument(
        "--labels",
        nargs='+',
        default=['Green', 'Purple'],
        help="List of class labels (default: Green Purple)"
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
        default=8,
        help="Batch size for training (default: 8)"
    )
    parser.add_argument(
        "--export-dir",
        default="/workspace/exported_model",
        help="Directory to export model and metadata"
    )
    
    args = parser.parse_args()

    # Validate inputs
    if not os.path.isdir(args.images):
        print(f"[ERROR] Training images directory not found: {args.images}")
        sys.exit(1)
    if not os.path.isdir(args.annotations):
        print(f"[ERROR] Training annotations directory not found: {args.annotations}")
        sys.exit(1)
    if not os.path.isdir(args.val_images):
        print(f"[ERROR] Validation images directory not found: {args.val_images}")
        sys.exit(1)
    if not os.path.isdir(args.val_annotations):
        print(f"[ERROR] Validation annotations directory not found: {args.val_annotations}")
        sys.exit(1)
    
    # Test set is optional but check if both dirs exist or neither
    test_available = os.path.isdir(args.test_images) and os.path.isdir(args.test_annotations)
    if not test_available:
        print(f"[WARN] Test set not found, skipping test evaluation")

    # Create export directory if needed
    os.makedirs(args.export_dir, exist_ok=True)

    print("=" * 70)
    print("TFLite Model Maker - Object Detection Training")
    print("=" * 70)
    print(f"Training images:       {args.images}")
    print(f"Training annotations:  {args.annotations}")
    print(f"Validation images:     {args.val_images}")
    print(f"Validation annotations:{args.val_annotations}")
    print(f"Class labels:          {args.labels}")
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

    print("\n[1/5] Loading training dataset from Pascal VOC annotations...")
    try:
        train_data = object_detector.DataLoader.from_pascal_voc(
            args.images,
            args.annotations,
            args.labels
        )
        print(f"[OK] Training dataset loaded: {len(train_data)} examples")
    except Exception as e:
        print(f"[ERROR] Failed to load training dataset: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("  - Check that image filenames match XML annotation filenames")
        print("  - Ensure XML files are valid Pascal VOC format")
        print("  - Verify XML files contain <object> and <bndbox> elements")
        sys.exit(1)

    print("\n[2/5] Loading validation dataset...")
    try:
        val_data = object_detector.DataLoader.from_pascal_voc(
            args.val_images,
            args.val_annotations,
            args.labels
        )
        print(f"[OK] Validation dataset loaded: {len(val_data)} examples")
    except Exception as e:
        print(f"[ERROR] Failed to load validation dataset: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n[3/5] Creating model specification...")
    try:
        spec = object_detector.EfficientDetLite0Spec()
        print("[OK] Using EfficientDet-Lite0 model spec")
    except Exception as e:
        print(f"[ERROR] Failed to load model spec: {e}")
        sys.exit(1)

    print("\n[4/5] Training object detection model...")
    print("This may take several minutes depending on dataset size and hardware...")
    try:
        model = object_detector.create(
            train_data,
            model_spec=spec,
            epochs=args.epochs,
            batch_size=args.batch_size,
            validation_data=val_data,
            train_whole_model=False
        )
        print("[OK] Training completed successfully")
    except Exception as e:
        print(f"[ERROR] Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n[5/5] Exporting TFLite model...")
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

    # Evaluate on test set if available
    if test_available:
        print("\n" + "=" * 70)
        print("Test Set Evaluation")
        print("=" * 70)
        
        print("\n[TEST] Loading test dataset...")
        try:
            test_data = object_detector.DataLoader.from_pascal_voc(
                args.test_images,
                args.test_annotations,
                args.labels
            )
            print(f"[OK] Test dataset loaded: {len(test_data)} examples")
        except Exception as e:
            print(f"[ERROR] Failed to load test dataset: {e}")
            import traceback
            traceback.print_exc()
            test_available = False
        
        if test_available:
            print("\n[TEST] Evaluating base model on test set...")
            try:
                loss, coco_metrics = model.evaluate(test_data)
                print(f"[OK] Base model evaluation complete")
                print(f"     Loss: {loss:.4f}")
                if coco_metrics:
                    print(f"     COCO metrics: {coco_metrics}")
            except Exception as e:
                print(f"[WARN] Base model evaluation failed: {e}")
            
            print("\n[TEST] Evaluating TFLite model on test set...")
            try:
                tflite_loss, tflite_coco = model.evaluate_tflite(args.output, test_data)
                print(f"[OK] TFLite model evaluation complete")
                print(f"     Loss: {tflite_loss:.4f}")
                if tflite_coco:
                    print(f"     COCO metrics: {tflite_coco}")
            except Exception as e:
                print(f"[WARN] TFLite evaluation failed: {e}")

    print("\n" + "=" * 70)
    print("Training completed successfully!")
    print(f"Model location: {os.path.abspath(args.output)}")
    if test_available:
        print("Test evaluation: COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
