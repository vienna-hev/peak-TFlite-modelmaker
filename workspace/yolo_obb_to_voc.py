#!/usr/bin/env python3
"""
Convert YOLO OBB (Oriented Bounding Box) format to Pascal VOC XML.
YOLO OBB format: x1 y1 x2 y2 x3 y3 x4 y4 class_name difficulty
We'll convert the rotated box to axis-aligned bounding box (AABB).
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom


def parse_yolo_obb_line(line):
    """Parse a single line of YOLO OBB format."""
    parts = line.strip().split()
    if len(parts) < 10:
        return None
    
    # Extract 4 corner points (x1,y1, x2,y2, x3,y3, x4,y4)
    try:
        coords = [float(parts[i]) for i in range(8)]
        class_name = parts[8]
        difficulty = int(parts[9])
        
        # Get axis-aligned bounding box from rotated box
        x_coords = [coords[0], coords[2], coords[4], coords[6]]
        y_coords = [coords[1], coords[3], coords[5], coords[7]]
        
        xmin = int(min(x_coords))
        ymin = int(min(y_coords))
        xmax = int(max(x_coords))
        ymax = int(max(y_coords))
        
        return {
            'class': class_name,
            'xmin': xmin,
            'ymin': ymin,
            'xmax': xmax,
            'ymax': ymax,
            'difficulty': difficulty
        }
    except (ValueError, IndexError):
        return None


def create_voc_xml(image_filename, image_width, image_height, objects, output_path):
    """Create Pascal VOC XML annotation file."""
    annotation = ET.Element('annotation')
    
    folder = ET.SubElement(annotation, 'folder')
    folder.text = 'images'
    
    filename = ET.SubElement(annotation, 'filename')
    filename.text = image_filename
    
    path = ET.SubElement(annotation, 'path')
    path.text = os.path.join('/workspace/data/images', image_filename)
    
    source = ET.SubElement(annotation, 'source')
    database = ET.SubElement(source, 'database')
    database.text = 'Unknown'
    
    size = ET.SubElement(annotation, 'size')
    width = ET.SubElement(size, 'width')
    width.text = str(image_width)
    height = ET.SubElement(size, 'height')
    height.text = str(image_height)
    depth = ET.SubElement(size, 'depth')
    depth.text = '3'
    
    segmented = ET.SubElement(annotation, 'segmented')
    segmented.text = '0'
    
    for obj in objects:
        obj_elem = ET.SubElement(annotation, 'object')
        
        name = ET.SubElement(obj_elem, 'name')
        name.text = obj['class']
        
        pose = ET.SubElement(obj_elem, 'pose')
        pose.text = 'Unspecified'
        
        truncated = ET.SubElement(obj_elem, 'truncated')
        truncated.text = '0'
        
        difficult = ET.SubElement(obj_elem, 'difficult')
        difficult.text = str(obj['difficulty'])
        
        bndbox = ET.SubElement(obj_elem, 'bndbox')
        xmin_elem = ET.SubElement(bndbox, 'xmin')
        xmin_elem.text = str(obj['xmin'])
        ymin_elem = ET.SubElement(bndbox, 'ymin')
        ymin_elem.text = str(obj['ymin'])
        xmax_elem = ET.SubElement(bndbox, 'xmax')
        xmax_elem.text = str(obj['xmax'])
        ymax_elem = ET.SubElement(bndbox, 'ymax')
        ymax_elem.text = str(obj['ymax'])
    
    # Pretty print
    xml_str = minidom.parseString(ET.tostring(annotation)).toprettyxml(indent="  ")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_str)


def convert_split(source_root, split_name, target_images_dir, target_annotations_dir, image_width=640, image_height=480):
    """Convert a single split (train/test/valid)."""
    label_dir = Path(source_root) / split_name / 'labelTxt'
    image_dir = Path(source_root) / split_name / 'images'
    
    if not label_dir.exists():
        print(f"[SKIP] {label_dir} not found")
        return 0, 0
    
    target_img_split = Path(target_images_dir) / split_name
    target_ann_split = Path(target_annotations_dir) / split_name
    target_img_split.mkdir(parents=True, exist_ok=True)
    target_ann_split.mkdir(parents=True, exist_ok=True)
    
    converted = 0
    skipped = 0
    
    for label_file in label_dir.glob('*.txt'):
        # Find corresponding image
        base_name = label_file.stem
        image_file = None
        for ext in ['.jpg', '.png', '.jpeg']:
            candidate = image_dir / f"{base_name}{ext}"
            if candidate.exists():
                image_file = candidate
                break
        
        if not image_file:
            print(f"[WARN] No image found for {label_file.name}")
            skipped += 1
            continue
        
        # Parse label file
        objects = []
        with open(label_file, 'r', encoding='utf-8') as f:
            for line in f:
                obj = parse_yolo_obb_line(line)
                if obj:
                    objects.append(obj)
        
        if not objects:
            print(f"[WARN] No valid objects in {label_file.name}")
            skipped += 1
            continue
        
        # Copy image
        import shutil
        target_img_path = target_img_split / image_file.name
        shutil.copy2(image_file, target_img_path)
        
        # Create XML
        xml_filename = base_name + '.xml'
        xml_path = target_ann_split / xml_filename
        create_voc_xml(image_file.name, image_width, image_height, objects, xml_path)
        
        converted += 1
    
    return converted, skipped


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Convert YOLO OBB dataset to Pascal VOC')
    parser.add_argument('--source', required=True, help='Path to YOLO dataset root (contains train/test/valid)')
    parser.add_argument('--target-images', default='/workspace/data/images', help='Target images directory')
    parser.add_argument('--target-annotations', default='/workspace/data/annotations', help='Target annotations directory')
    parser.add_argument('--width', type=int, default=640, help='Image width (default: 640)')
    parser.add_argument('--height', type=int, default=480, help='Image height (default: 480)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("YOLO OBB → Pascal VOC Converter")
    print("=" * 70)
    print(f"Source:      {args.source}")
    print(f"Images:      {args.target_images}")
    print(f"Annotations: {args.target_annotations}")
    print(f"Image size:  {args.width}x{args.height}")
    print("=" * 70)
    
    total_converted = 0
    total_skipped = 0
    
    for split in ['train', 'test', 'valid']:
        print(f"\n[{split.upper()}]")
        converted, skipped = convert_split(
            args.source, 
            split, 
            args.target_images, 
            args.target_annotations,
            args.width,
            args.height
        )
        print(f"  Converted: {converted}")
        print(f"  Skipped:   {skipped}")
        total_converted += converted
        total_skipped += skipped
    
    print("\n" + "=" * 70)
    print(f"Total converted: {total_converted}")
    print(f"Total skipped:   {total_skipped}")
    print("=" * 70)


if __name__ == '__main__':
    main()
