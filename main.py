import os
import json
from shapely.geometry import Polygon
import xml.etree.ElementTree as ET
from xml.dom import minidom
annotations_path = "/home/can/Desktop/Python/monkey-model/new_annotations/json_pixel"
annotations_out_path = "/home/can/Desktop/Python/monkey-model/patch_annotations/xml"
patch_size = 1024
step = 64

os.makedirs(annotations_out_path, exist_ok=True)
i = 1
next_patch_id = 0


def generate_patches(x_offset, y_offset):
    patches = []
    patch_id = next_patch_id
    for y in range(min_y + y_offset, max_y, patch_size):
        for x in range(min_x + x_offset, max_x, patch_size):
            patch_box = Polygon(
                [
                    (x, y),
                    (x + patch_size, y),
                    (x + patch_size, y + patch_size),
                    (x, y + patch_size),
                ]
            )
            if roi_shape.contains(patch_box):
                patches.append({"id": patch_id, "x": x, "y": y})
                patch_id += 1
    return patches


for fileName in os.listdir(annotations_path):
    if not fileName.endswith("inflammatory-cells.json"):
        continue
    file_path = os.path.join(annotations_path, fileName)
    out_file_path = os.path.join(
        annotations_out_path, fileName.replace(".json", ".xml"))
    with open(file_path, "r") as f:
        data = json.load(f)
    asap_annotation = ET.Element("ASAP_Annotations")
    annotations = ET.SubElement(asap_annotation, "Annotations")
    next_patch_id = 0
    for roi in data["rois"]:
        roi_polygon = roi["polygon"]
        roi_shape = Polygon(roi_polygon)
        min_x, min_y, max_x, max_y = map(int, roi_shape.bounds)
        best_patches = []
        max_patches = 0
        best_offsets = (0, 0)
        for x_offset in range(0, patch_size, step):
            for y_offset in range(0, patch_size, step):
                patches = generate_patches(x_offset, y_offset)
                if len(patches) > max_patches:
                    print(f"New max patches: {len(patches)}")
                    max_patches = len(patches)
                    best_patches = patches.copy()
                    best_offsets = (x_offset, y_offset)
        next_patch_id += len(best_patches)
        for patch in best_patches:
            centerAnnotation = ET.SubElement(annotations, "Annotation")
            centerAnnotation.set("Name", f"Center_{patch['id']}")
            centerAnnotation.set("Type", "Dot")
            centerAnnotation.set("PartOfGroup", "None")
            centerAnnotation.set("Color", "255, 0, 0")
            centerCoordinates = ET.SubElement(centerAnnotation, "Coordinates")
            centerCoordinate = ET.SubElement(centerCoordinates, "Coordinate")
            centerCoordinate.set("X", str(patch["x"] + patch_size // 2))
            centerCoordinate.set("Y", str(patch["y"] + patch_size // 2))
            annotation = ET.SubElement(annotations, "Annotation")
            annotation.set("Name", f"Patch_{patch['id']}")
            annotation.set("Type", "Rectangle")
            annotation.set("PartOfGroup", "None")
            annotation.set("Color", "255, 0, 0")
            coordinates = ET.SubElement(annotation, "Coordinates")
            order = 0
            for point in [
                (patch["x"], patch["y"]),
                (patch["x"] + patch_size, patch["y"]),
                (patch["x"] + patch_size, patch["y"] + patch_size),
                (patch["x"], patch["y"] + patch_size)
            ]:
                coordinate = ET.SubElement(coordinates, "Coordinate")
                coordinate.set("Order", str(order))
                coordinate.set("X", str(point[0]))
                coordinate.set("Y", str(point[1]))
                order += 1
        roi_annotation = ET.SubElement(annotations, "Annotation")
        roi_annotation.set("Name", f"ROI_{i}")
        roi_annotation.set("Type", "Polygon")
        roi_annotation.set("PartOfGroup", "None")
        roi_annotation.set("Color", "#73d216")
        i += 1
        roi_coordinates = ET.SubElement(roi_annotation, "Coordinates")
        roi_order = 0
        for coordinate in roi_polygon:
            roi_coordinate = ET.SubElement(roi_coordinates, "Coordinate")
            roi_coordinate.set("Order", str(roi_order))
            roi_coordinate.set("X", str(coordinate[0]))
            roi_coordinate.set("Y", str(coordinate[1]))
            roi_order += 1
    dom = minidom.parseString(ET.tostring(asap_annotation))
    xml_str_pretty = dom.toprettyxml(indent="\t")
    with open(out_file_path, "wb") as f:
        f.write(xml_str_pretty.encode())
