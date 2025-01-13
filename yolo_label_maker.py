import os
import xml.etree.ElementTree as ET

patch_annotations_path = "S:/GrandChallenge/Monkey/Dataset2/pure_patches/patch_annotations"  
cell_annotations_path = "annotations/xml"    
labels_out_path = "S:/GrandChallenge/Monkey/Dataset2/pure_patches/labels"                      


patch_size = 512
#box_sizes = {"lymphocytes": 16, "monocytes": 42}  # Box sizes for each cell type
box_sizes = {"lymphocytes": 0.0361, "monocytes": 0.039}
monocyte = 1  # YOLO class ID for monocytes
lymphocyte = 0  # YOLO class ID for lymphocytes

# Create output directory if it doesn't exist
os.makedirs(labels_out_path, exist_ok=True)

def parse_patch_annotations(xml_path):
    """Parse the XML file to extract patch locations."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    patches = {}

    for annotation in root.find("Annotations").findall("Annotation"):
        if annotation.get("Name").startswith("Patch"):
            patch_number = int(annotation.get("Name").split("_")[1])
            coordinates = annotation.find("Coordinates").findall("Coordinate")
            x_min = int(float(coordinates[0].get("X")))
            y_min = int(float(coordinates[0].get("Y")))
            patches[patch_number] = (x_min, y_min)
    return patches

def parse_cell_annotations(xml_path):
    """Parse the XML file to extract cell coordinates and types."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    cells = []

    for annotation in root.find("Annotations").findall("Annotation"):
        if annotation.get("Type") == "Dot":
            part_of_group = annotation.get("PartOfGroup")
            if part_of_group not in box_sizes:
                continue
            coordinates = annotation.find("Coordinates").find("Coordinate")
            x = int(float(coordinates.get("X")))
            y = int(float(coordinates.get("Y")))
            cells.append((x, y, part_of_group))
    return cells

def normalize_coordinates(x, y, box_size, patch_x, patch_y, patch_size):
    """Normalize coordinates to YOLO format."""
    x_center = (x - patch_x) / patch_size
    y_center = (y - patch_y) / patch_size
    #width = box_size / patch_size
    width = box_size
    height = box_size
    #height = box_size / patch_size
    return x_center, y_center, width, height

# Process each patch annotation file
for patch_file in os.listdir(patch_annotations_path):
    if not patch_file.endswith(".xml"):
        continue

    patch_xml_path = os.path.join(patch_annotations_path, patch_file)
    patches = parse_patch_annotations(patch_xml_path)

    slide_name = patch_file.split("_")[0] + "_" + patch_file.split("_")[1]  # E.g., "A_P000001"
    cell_xml_path = os.path.join(cell_annotations_path, f"{slide_name}.xml")

    if not os.path.exists(cell_xml_path):
        print(f"Cell annotation file not found: {cell_xml_path}")
        continue

    cells = parse_cell_annotations(cell_xml_path)

    # Generate YOLO labels for each patch
    for patch_number, (patch_x, patch_y) in patches.items():
        label_lines = []

        for x, y, cell_type in cells:
            if patch_x <= x < patch_x + patch_size and patch_y <= y < patch_y + patch_size:
                box_size = box_sizes[cell_type]
                class_id = lymphocyte if cell_type == "lymphocytes" else monocyte
                x_center, y_center, width, height = normalize_coordinates(
                    x, y, box_size, patch_x, patch_y, patch_size
                )
                label_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.4f} {height:.4f}")

        label_file = os.path.join(labels_out_path, f"{slide_name}_inflammatory-cells_{patch_number}.txt")
        with open(label_file, "w") as f:
            f.write("\n".join(label_lines))

        print(f"Processed {slide_name}_Patch_{patch_number}: {len(label_lines)} cells")
