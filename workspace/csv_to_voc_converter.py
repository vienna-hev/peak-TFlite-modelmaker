#!/usr/bin/env python3
"""
csv_to_voc_converter.py

Converts a CSV annotation file (with bbox_x, bbox_y, bbox_width, bbox_height format)
to Pascal VOC XML format.

The converter:
1. Groups annotations by image name
2. Creates one XML file per image
3. Converts bbox format: (x, y, width, height) → (xmin, ymin, xmax, ymax)
4. Saves XML files to the annotations directory

Usage:
    python csv_to_voc_converter.py \\
        --csv-file C:\\Users\\heven\\Downloads\\annotations.csv \\
        --output-dir C:\\Users\\Vienna\\take68\\workspace\\data\\annotations \\
        --images-dir C:\\Users\\Vienna\\take68\\workspace\\data\\images
"""

import csv
import os
import sys
import argparse
from collections import defaultdict
import xml.etree.ElementTree as ET


def convert_csv_to_voc(csv_file, output_dir, images_dir=None):
    """
    Convert CSV annotations to Pascal VOC XML format.
    
    Args:
        csv_file: Path to CSV file with columns: label_name, bbox_x, bbox_y, 
                  bbox_width, bbox_height, image_name, image_width, image_height
        output_dir: Directory to write XML files
        images_dir: Optional directory containing images (for validation)
    """
    
    if not os.path.exists(csv_file):
        print(f"[ERROR] CSV file not found: {csv_file}")
        sys.exit(1)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Group annotations by image
    annotations_by_image = defaultdict(lambda: {
        'objects': [],
        'width': None,
        'height': None
    })
    
    print(f"[1/3] Reading CSV file: {csv_file}")
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            # Skip header rows (sometimes there are duplicates)
            row_count = 0
            for row in reader:
                # Skip empty rows or header duplicates
                if not row.get('image_name') or row['image_name'].startswith('image_name'):
                    continue
                
                try:
                    label = row['label_name'].strip()
                    bbox_x = int(row['bbox_x'].strip())
                    bbox_y = int(row['bbox_y'].strip())
                    bbox_width = int(row['bbox_width'].strip())
                    bbox_height = int(row['bbox_height'].strip())
                    image_name = row['image_name'].strip()
                    image_width = int(row['image_width'].strip())
                    image_height = int(row['image_height'].strip())
                    
                    # Convert (x, y, width, height) → (xmin, ymin, xmax, ymax)
                    xmin = bbox_x
                    ymin = bbox_y
                    xmax = bbox_x + bbox_width
                    ymax = bbox_y + bbox_height
                    
                    # Store annotation
                    annotations_by_image[image_name]['objects'].append({
                        'name': label,
                        'xmin': xmin,
                        'ymin': ymin,
                        'xmax': xmax,
                        'ymax': ymax
                    })
                    annotations_by_image[image_name]['width'] = image_width
                    annotations_by_image[image_name]['height'] = image_height
                    
                    row_count += 1
                except (ValueError, KeyError) as e:
                    print(f"[WARN] Skipping malformed row: {e}")
                    continue
    
    except Exception as e:
        print(f"[ERROR] Failed to read CSV: {e}")
        sys.exit(1)
    
    print(f"[OK] Read {row_count} annotations for {len(annotations_by_image)} images")
    
    # Generate XML files
    print(f"[2/3] Generating XML files...")
    
    xml_count = 0
    for image_name, data in annotations_by_image.items():
        # Create XML structure
        annotation = ET.Element('annotation')
        
        # Filename
        filename_elem = ET.SubElement(annotation, 'filename')
        filename_elem.text = image_name
        
        # Folder (optional)
        folder_elem = ET.SubElement(annotation, 'folder')
        folder_elem.text = 'images'
        
        # Size
        size_elem = ET.SubElement(annotation, 'size')
        width_elem = ET.SubElement(size_elem, 'width')
        width_elem.text = str(data['width'])
        height_elem = ET.SubElement(size_elem, 'height')
        height_elem.text = str(data['height'])
        depth_elem = ET.SubElement(size_elem, 'depth')
        depth_elem.text = '3'
        
        # Objects
        for obj in data['objects']:
            obj_elem = ET.SubElement(annotation, 'object')
            
            name_elem = ET.SubElement(obj_elem, 'name')
            name_elem.text = obj['name']
            
            bndbox_elem = ET.SubElement(obj_elem, 'bndbox')
            xmin_elem = ET.SubElement(bndbox_elem, 'xmin')
            xmin_elem.text = str(obj['xmin'])
            ymin_elem = ET.SubElement(bndbox_elem, 'ymin')
            ymin_elem.text = str(obj['ymin'])
            xmax_elem = ET.SubElement(bndbox_elem, 'xmax')
            xmax_elem.text = str(obj['xmax'])
            ymax_elem = ET.SubElement(bndbox_elem, 'ymax')
            ymax_elem.text = str(obj['ymax'])
        
        # Write to file
        xml_filename = os.path.splitext(image_name)[0] + '.xml'
        xml_path = os.path.join(output_dir, xml_filename)
        
        try:
            tree = ET.ElementTree(annotation)
            ET.indent(tree, space='  ')  # Pretty print (Python 3.9+)
            tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            xml_count += 1
        except Exception as e:
            print(f"[ERROR] Failed to write {xml_path}: {e}")
    
    print(f"[OK] Generated {xml_count} XML files")
    
    # Validate (optional)
    if images_dir and os.path.isdir(images_dir):
        print(f"[3/3] Validating image/annotation pairs...")
        
        image_files = set(os.path.splitext(f)[0] for f in os.listdir(images_dir) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')))
        xml_files = set(os.path.splitext(f)[0] for f in os.listdir(output_dir) 
                       if f.endswith('.xml'))
        
        matched = image_files & xml_files
        missing_images = xml_files - image_files
        missing_xmls = image_files - xml_files
        
        print(f"[OK] {len(matched)} image/annotation pairs matched")
        
        if missing_images:
            print(f"[WARN] {len(missing_images)} XMLs without images: {list(missing_images)[:3]}...")
        if missing_xmls:
            print(f"[WARN] {len(missing_xmls)} images without XMLs: {list(missing_xmls)[:3]}...")
    else:
        print(f"[3/3] Skipping validation (images directory not provided)")
    
    print("\n" + "=" * 70)
    print(f"Conversion complete!")
    print(f"XML files saved to: {output_dir}")
    print("=" * 70)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert CSV annotations to Pascal VOC XML format'
    )
    parser.add_argument(
        '--csv-file',
        required=True,
        help='Path to CSV annotation file'
    )
    parser.add_argument(
        '--output-dir',
        required=True,
        help='Directory to write XML files'
    )
    parser.add_argument(
        '--images-dir',
        default=None,
        help='Optional: directory containing images for validation'
    )
    
    args = parser.parse_args()
    
    convert_csv_to_voc(
        csv_file=args.csv_file,
        output_dir=args.output_dir,
        images_dir=args.images_dir
    )
