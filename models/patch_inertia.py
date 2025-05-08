import os
import xml.etree.ElementTree as ET

REQUIRED_INERTIA_TAGS = {
    'ixx': '0.01',
    'iyy': '0.01',
    'izz': '0.01',
    'ixy': '0.0',
    'ixz': '0.0',
    'iyz': '0.0',
}

def patch_models(model_dir):
    for root, _, files in os.walk(model_dir):
        for filename in files:
            if not filename.endswith('.sdf'):
                continue

            path = os.path.join(root, filename)
            model_name = root[2:]
            if model_name.startswith("aws_robomaker_residential_"):
                descriptor = model_name.replace("aws_robomaker_residential_", "")
            else:
                descriptor = model_name
                
            try:
                tree = ET.parse(path)
                root_el = tree.getroot()
                modified = False

                for link in root_el.findall('.//link'):
                    # Rename generic link
                    if link.get('name') == 'link':
                        link.set('name', f'link_{descriptor}')
                        modified = True

                    inertial = link.find('inertial')
                    if inertial is not None:
                        inertia = inertial.find('inertia')
                        if inertia is None:
                            # Add new inertia block
                            inertia = ET.SubElement(inertial, 'inertia')
                            for tag, val in REQUIRED_INERTIA_TAGS.items():
                                ET.SubElement(inertia, tag).text = val
                            print(f"Added missing <inertia> in {path}")
                            modified = True
                        else:
                            # Validate and fix duplicates/missing tags
                            seen = {}
                            for child in list(inertia):
                                if child.tag in seen:
                                    inertia.remove(child)
                                    print(f"Removed duplicate <{child.tag}> in {path}")
                                    modified = True
                                else:
                                    seen[child.tag] = child

                            # Fill in missing tags
                            for tag, val in REQUIRED_INERTIA_TAGS.items():
                                if tag not in seen:
                                    ET.SubElement(inertia, tag).text = val
                                    print(f"Added missing <{tag}> in {path}")
                                    modified = True

                if modified:
                    tree.write(path)
                    print(f"Patched: {path}")

            except ET.ParseError:
                print(f"Failed to parse XML: {path}")
              

if __name__ == '__main__':
    patch_models('.')
