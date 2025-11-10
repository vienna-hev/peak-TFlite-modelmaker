#!/usr/bin/env python3
"""
check_training_env.py

Checks whether the environment + dataset look ready for TFLite Model Maker object detection training.

Exit codes:
  0 = all critical checks passed
  1 = one or more critical failures
"""

import sys
import os
import argparse
import glob
import xml.etree.ElementTree as ET
import shutil
import importlib
from importlib import util
from importlib import metadata

CRITICAL_FAIL = False

def fail(msg):
    global CRITICAL_FAIL
    CRITICAL_FAIL = True
    print("[FAIL] " + msg)

def ok(msg):
    print("[OK]   " + msg)

def warn(msg):
    print("[WARN] " + msg)

def check_python(min_major=3, min_minor=8):
    py = sys.version_info
    if (py.major, py.minor) < (min_major, min_minor):
        fail(f"Python {min_major}.{min_minor}+ required. Found {py.major}.{py.minor}.")
    else:
        ok(f"Python OK: {py.major}.{py.minor}")

def try_import(module_name, friendly=None):
    friendly = friendly or module_name
    try:
        mod = importlib.import_module(module_name)
        ver = getattr(mod, "__version__", None)
        if not ver:
            try:
                ver = metadata.version(module_name)
            except Exception:
                ver = "unknown"
        ok(f"Imported {friendly} (version: {ver})")
        return mod, ver
    except Exception as e:
        fail(f"Cannot import {friendly}: {type(e).__name__}: {e}")
        return None, None

def check_tensorflow():
    mod, ver = try_import("tensorflow", "tensorflow")
    if mod:
        try:
            gpus = mod.config.list_physical_devices('GPU')
            if gpus:
                ok(f"TensorFlow sees GPUs: {len(gpus)} device(s).")
            else:
                warn("TensorFlow did not find GPU devices (CPU-only). This is OK but slower.")
            ok(f"TensorFlow version: {ver}")
        except Exception as e:
            warn(f"Could not query GPU devices: {e}")
    return mod

def check_tflite_model_maker():
    mod, ver = try_import("tflite_model_maker", "tflite_model_maker")
    if mod:
        # try to import object_detector api used by training script
        try:
            from tflite_model_maker import object_detector
            ok("tflite_model_maker.object_detector import OK")
        except Exception as e:
            fail(f"tflite_model_maker.object_detector import failed: {type(e).__name__}: {e}")
    return mod

def check_optional(name):
    # Optional imports should not set the global critical-failure flag.
    friendly = name
    try:
        mod = importlib.import_module(name)
        ver = getattr(mod, "__version__", None)
        if not ver:
            try:
                ver = metadata.version(name)
            except Exception:
                ver = "unknown"
        ok(f"Imported {friendly} (version: {ver})")
        return True
    except Exception as e:
        # Report as a warning, do not mark CRITICAL_FAIL
        warn(f"Optional package not importable: {friendly}: {type(e).__name__}: {e}")
        return False

def list_images(images_dir):
    patterns = ("*.jpg","*.jpeg","*.png","*.bmp")
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(images_dir, p)))
    files = sorted(files)
    return files

def list_xmls(ann_dir):
    return sorted(glob.glob(os.path.join(ann_dir, "*.xml")))

def parse_voc_xml(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        objs = []
        for obj in root.findall('object'):
            name = obj.find('name')
            bndbox = obj.find('bndbox')
            if name is None:
                continue
            label = name.text.strip()
            if bndbox is None:
                bbox = None
            else:
                bbox = tuple(int(float(bndbox.find(x).text)) for x in ('xmin','ymin','xmax','ymax'))
            objs.append((label, bbox))
        return objs
    except Exception as e:
        return f"PARSE_ERROR: {e}"

def check_dataset(images_dir, annotations_dir, min_images):
    if not os.path.isdir(images_dir):
        fail(f"Images directory not found: {images_dir}")
        return
    if not os.path.isdir(annotations_dir):
        fail(f"Annotations directory not found: {annotations_dir}")
        return

    images = list_images(images_dir)
    xmls = list_xmls(annotations_dir)

    ok(f"Found {len(images)} images and {len(xmls)} annotation XML files.")

    if len(images) < min_images:
        warn(f"Only {len(images)} images. Recommended at least {min_images} for meaningful training.")

    # match by basename
    image_basenames = {os.path.splitext(os.path.basename(p))[0] for p in images}
    xml_basenames = {os.path.splitext(os.path.basename(p))[0] for p in xmls}
    common = image_basenames & xml_basenames
    if len(common) == 0:
        fail("No matching image/annotation basenames found. Make sure XMLs match image filenames (e.g. img_001.jpg <-> img_001.xml).")
    else:
        ok(f"{len(common)} images have matching XML annotations.")

    # parse first few xmls
    labels_seen = set()
    errors = 0
    for xml in xmls[:5]:
        res = parse_voc_xml(xml)
        if isinstance(res, str) and res.startswith("PARSE_ERROR"):
            warn(f"Could not parse {xml}: {res}")
            errors += 1
        else:
            for label, bbox in res:
                labels_seen.add(label)
            ok(f"Parsed {xml} -> {len(res)} objects, labels: {list({l for l,_ in res})[:5]}")

    if errors > 0:
        warn(f"Found {errors} XML parse errors in first {min(5, len(xmls))} files.")

    if labels_seen:
        ok(f"Inferred labels from sample annotations: {sorted(labels_seen)}")
    else:
        warn("No labels inferred from XMLs (maybe XML structure differs).")

def check_disk_space(path, min_bytes=1_000_000_000):
    try:
        usage = shutil.disk_usage(path)
        free = usage.free
        if free < min_bytes:
            warn(f"Low disk space at {path}: {free/1e9:.2f} GB free. Recommended at least {min_bytes/1e9:.1f} GB.")
        else:
            ok(f"Disk free at {path}: {free/1e9:.2f} GB")
    except Exception as e:
        warn(f"Could not query disk space for {path}: {e}")

def check_export_dir(export_dir):
    if not os.path.exists(export_dir):
        try:
            os.makedirs(export_dir, exist_ok=True)
            ok(f"Created export dir: {export_dir}")
        except Exception as e:
            fail(f"Cannot create export dir {export_dir}: {e}")
    else:
        ok(f"Export dir exists: {export_dir}")
    check_disk_space(export_dir, min_bytes=1_000_000_000)

def check_pip_packages(names):
    # best-effort: use importlib.metadata to fetch versions
    results = {}
    for name in names:
        try:
            v = metadata.version(name)
            ok(f"Package installed: {name}=={v}")
            results[name] = v
        except Exception:
            warn(f"Package not found (pip): {name}")
            results[name] = None
    return results

def main():
    p = argparse.ArgumentParser(description="Check TFLite Model Maker training readiness.")
    p.add_argument("--images", default="/workspace/data/images", help="images directory (Pascal VOC)")
    p.add_argument("--annotations", default="/workspace/data/annotations", help="Pascal VOC XMLs directory")
    p.add_argument("--export", default="/workspace/exported_model", help="export output directory")
    p.add_argument("--min-images", type=int, default=10, help="minimum recommended images")
    args = p.parse_args()

    print("=== ENV CHECK START ===")
    check_python(3,8)
    tf_mod = check_tensorflow()
    tflmm = check_tflite_model_maker()

    # optional modules that are useful (not fatal)
    optional_list = ["tf_models_official", "scann", "pycocotools"]
    for opt in optional_list:
        check_optional(opt)

    check_dataset(args.images, args.annotations, args.min_images)
    check_export_dir(args.export)

    # pip-side checks for some important packages
    check_pip_packages([
        "tflite-model-maker",
        "tensorflow",
        "tf-models-official",
        "scann",
        "pycocotools"
    ])

    print("=== ENV CHECK FINISHED ===")
    if CRITICAL_FAIL:
        print("\nOne or more critical checks failed. Fix them before training.")
        sys.exit(1)
    else:
        print("\nAll critical checks passed. You should be able to start training (modulo runtime resources).")
        sys.exit(0)

if __name__ == "__main__":
    main()

