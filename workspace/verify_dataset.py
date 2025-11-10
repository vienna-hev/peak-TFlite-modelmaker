#!/usr/bin/env python3
"""
Verify Pascal VOC XML annotations and generate basic statistics.
Run this locally (without Docker) to validate your dataset before training.

Usage:
    python verify_dataset.py
    python verify_dataset.py --images path/to/images --annotations path/to/annotations
"""

import os
import sys
import glob
import xml.etree.ElementTree as ET
import argparse
from collections import defaultdict
from pathlib import Path

def verify_image_exists(xml_path, image_dir):
    """Check if the image referenced in XML exists."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        filename = root.find('filename')
        if filename is not None:
            image_path = os.path.join(image_dir, filename.text)
            return os.path.exists(image_path), filename.text, image_path
    except Exception as e:
        return False, None, str(e)
    return False, None, "No filename element found"

def extract_labels(xml_path):
    """Extract all object labels from an XML file."""
    labels = []
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for obj in root.findall('object'):
            name_elem = obj.find('name')
            if name_elem is not None:
                labels.append(name_elem.text)
    except Exception as e:
        return None, str(e)
    return labels, None

def get_image_files(image_dir, extensions=('jpg', 'jpeg', 'png', 'bmp')):
    """Get all image files in a directory."""
    images = []
    for ext in extensions:
        images.extend(glob.glob(os.path.join(image_dir, f"*.{ext}")))
        images.extend(glob.glob(os.path.join(image_dir, f"*.{ext.upper()}")))
    return sorted(set(images))

def get_annotation_files(annotation_dir):
    """Get all XML annotation files."""
    return sorted(glob.glob(os.path.join(annotation_dir, "*.xml")))

def main():
    parser = argparse.ArgumentParser(description="Verify Pascal VOC dataset format")
    parser.add_argument("--images", default="workspace/data/images", help="Images directory")
    parser.add_argument("--annotations", default="workspace/data/annotations", help="Annotations directory")
    args = parser.parse_args()

    print("=" * 70)
    print("Pascal VOC Dataset Verification")
    print("=" * 70)
    print(f"Images dir:       {os.path.abspath(args.images)}")
    print(f"Annotations dir:  {os.path.abspath(args.annotations)}")
    print()

    # Check directories exist
    if not os.path.isdir(args.images):
        print(f"[ERROR] Images directory not found: {args.images}")
        sys.exit(1)
    if not os.path.isdir(args.annotations):
        print(f"[ERROR] Annotations directory not found: {args.annotations}")
        sys.exit(1)

    # Get files
    images = get_image_files(args.images)
    xmls = get_annotation_files(args.annotations)

    print(f"Found {len(images)} image files")
    print(f"Found {len(xmls)} annotation XML files")
    print()

    if len(images) == 0:
        print("[WARNING] No images found!")
    if len(xmls) == 0:
        print("[WARNING] No XML annotations found!")

    if len(images) == 0 or len(xmls) == 0:
        sys.exit(1)

    # Check matching files
    image_basenames = {os.path.splitext(os.path.basename(p))[0]: p for p in images}
    xml_basenames = {os.path.splitext(os.path.basename(p))[0]: p for p in xmls}

    common = set(image_basenames.keys()) & set(xml_basenames.keys())
    only_images = set(image_basenames.keys()) - set(xml_basenames.keys())
    only_xmls = set(xml_basenames.keys()) - set(image_basenames.keys())

    print(f"Matching pairs:   {len(common)}")
    print(f"Images without XML: {len(only_images)}")
    print(f"XMLs without images: {len(only_xmls)}")
    print()

    if len(only_images) > 0:
        print("[WARNING] Images without annotations:")
        for name in sorted(list(only_images))[:5]:
            print(f"  - {name}")
        if len(only_images) > 5:
            print(f"  ... and {len(only_images) - 5} more")

    if len(only_xmls) > 0:
        print("[WARNING] Annotations without images:")
        for name in sorted(list(only_xmls))[:5]:
            print(f"  - {name}")
        if len(only_xmls) > 5:
            print(f"  ... and {len(only_xmls) - 5} more")

    print()
    print("-" * 70)
    print("Checking annotation format...")
    print("-" * 70)

    all_labels = defaultdict(int)
    annotation_errors = 0
    image_errors = 0

    for xml_name in sorted(list(common))[:10]:  # Check first 10
        xml_path = xml_basenames[xml_name]
        image_path = image_basenames[xml_name]

        # Check image exists
        image_exists, referenced_name, resolved_path = verify_image_exists(xml_path, args.images)
        if not image_exists:
            image_errors += 1
            print(f"[WARN] {xml_name}: Image not found - {referenced_name}")

        # Extract labels
        labels, error = extract_labels(xml_path)
        if error:
            annotation_errors += 1
            print(f"[ERROR] {xml_name}: {error}")
        else:
            for label in labels:
                all_labels[label] += 1
            print(f"[OK]   {xml_name}: {len(labels)} objects, labels: {set(labels)}")

    print()
    if len(common) > 10:
        print(f"(Showing first 10 of {len(common)} files)")

    print()
    print("-" * 70)
    print("Label Summary")
    print("-" * 70)
    if all_labels:
        for label, count in sorted(all_labels.items(), key=lambda x: -x[1]):
            print(f"  {label:20s}: {count:4d} objects")
        print()
        print(f"Total unique labels: {len(all_labels)}")
        print(f"Total objects: {sum(all_labels.values())}")
    else:
        print("[WARNING] No labels found in annotations!")

    print()
    print("=" * 70)
    if annotation_errors == 0 and image_errors == 0 and len(common) > 0:
        print("[OK] Dataset format looks good!")
        print(f"Ready to train with {len(common)} image/annotation pairs")
        sys.exit(0)
    else:
        print("[WARNING] Dataset has issues (see above)")
        if annotation_errors > 0:
            print(f"  - {annotation_errors} annotation parsing errors")
        if image_errors > 0:
            print(f"  - {image_errors} missing image errors")
        if len(common) == 0:
            print("  - No matching image/annotation pairs!")
        sys.exit(1)

if __name__ == "__main__":
    main()
