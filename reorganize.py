#!/usr/bin/env python3
"""Reorganize output/ folder structure and fix all internal links.

Strategy:
1. Move top-level topic folders into bucket folders
2. All deeply nested content moves WITH its parent (preserving internal structure)
3. Update relative links in ALL .md files to reflect new paths
4. Update image paths (../src/ -> adjusted relative path to src/)

The key insight: links inside .md files are RELATIVE to the file's location.
When we move a folder, all files inside it move together, so links WITHIN
that subtree stay valid. Only links that CROSS between different top-level
folders need updating, plus the root index file and image paths.
"""

import os
import re
import shutil

OUTPUT = "output"
OLD_ROOT = os.path.join(OUTPUT, "01_articles_on_computer_science_subjects_gq")

# Mapping: old folder name -> (bucket, new folder name)
MOVE_MAP = {
    "01_computer_fundamentals_tutorial": ("01_Computer_Science_Foundations", "Computer_Fundamentals"),
    "02_engineering_mathematics_tutorials": ("01_Computer_Science_Foundations", "Engineering_Mathematics"),
    "03_mathematics_for_computer_science": ("01_Computer_Science_Foundations", "Mathematics_for_CS"),
    "04_operating_systems": ("02_Systems_and_Architecture", "Operating_Systems"),
    "05_computer_organization_and_architecture_tutorials": ("02_Systems_and_Architecture", "Computer_Organization"),
    "06_computer_network_tutorials": ("03_Networking_and_Security", "Computer_Networks"),
    "07_theory_of_computation_automata_tutorials": ("04_Theory_and_Compilers", "Theory_of_Computation"),
    "08_compiler_design_tutorials": ("04_Theory_and_Compilers", "Compiler_Design"),
    "09_distributed_systems_tutorial": ("02_Systems_and_Architecture", "Distributed_Systems"),
    "10_linux_tutorial": ("03_Networking_and_Security", "Linux"),
    "11_cyber_security_tutorial": ("03_Networking_and_Security", "Cyber_Security"),
    "12_dbms": ("05_Databases", "DBMS"),
    "13_data_warehousing_tutorial": ("05_Databases", "Data_Warehousing"),
    "14_machine_learning": ("06_AI_and_Machine_Learning", "Machine_Learning"),
    "15_artificial_intelligence": ("06_AI_and_Machine_Learning", "Artificial_Intelligence"),
    "16_data_analysis_tutorial": ("07_Data_Science_and_Analytics", "Data_Analysis"),
    "17_data_science_with_python_tutorial": ("07_Data_Science_and_Analytics", "Data_Science_with_Python"),
    "18_software_engineering": ("08_Software_Engineering", "Software_Engineering"),
    "19_software_testing_tutorial": ("08_Software_Engineering", "Software_Testing"),
    "20_web_technology": ("09_Web_Technology", "Web_Technology"),
}


def build_path_mapping():
    """Build old_path -> new_path mapping for every moved directory and file."""
    mapping = {}  # old_abs_path -> new_abs_path

    for old_name, (bucket, new_name) in MOVE_MAP.items():
        old_dir = os.path.join(OLD_ROOT, old_name)
        new_dir = os.path.join(OUTPUT, bucket, new_name)

        if not os.path.isdir(old_dir):
            continue

        # Map the directory itself
        mapping[old_dir] = new_dir

        # Map the corresponding .md file (sibling of the directory)
        old_md = old_dir + ".md"
        new_md = new_dir + ".md"
        if os.path.isfile(old_md):
            mapping[old_md] = new_md

        # Map all files/dirs inside recursively
        for root, dirs, files in os.walk(old_dir):
            rel = os.path.relpath(root, old_dir)
            new_root = os.path.join(new_dir, rel) if rel != "." else new_dir
            for f in files:
                old_f = os.path.join(root, f)
                new_f = os.path.join(new_root, f)
                mapping[old_f] = new_f

    return mapping


def move_folders():
    """Move folders to new locations."""
    for old_name, (bucket, new_name) in MOVE_MAP.items():
        old_dir = os.path.join(OLD_ROOT, old_name)
        new_dir = os.path.join(OUTPUT, bucket, new_name)

        if not os.path.isdir(old_dir):
            print(f"  SKIP (not found): {old_dir}")
            continue

        os.makedirs(os.path.dirname(new_dir), exist_ok=True)
        shutil.move(old_dir, new_dir)
        print(f"  MOVED: {old_name} -> {bucket}/{new_name}")

        # Also move the sibling .md file
        old_md = old_dir + ".md"
        new_md = new_dir + ".md"
        if os.path.isfile(old_md):
            shutil.move(old_md, new_md)
            print(f"  MOVED: {old_name}.md -> {bucket}/{new_name}.md")


def fix_links_in_file(filepath, path_mapping):
    """Fix relative links in a single .md file.

    Handles:
    - [text](relative/path.md) links
    - ![alt](relative/path/to/image) image links
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, OSError):
        return False

    file_dir = os.path.dirname(filepath)
    changed = False

    def replace_link(match):
        nonlocal changed
        prefix = match.group(1)  # [text]( or ![alt](
        rel_path = match.group(2)
        suffix = match.group(3)  # )

        # Resolve the old absolute path
        old_abs = os.path.normpath(os.path.join(file_dir, rel_path))

        # Check if this path was moved
        new_abs = path_mapping.get(old_abs)
        if new_abs is None:
            return match.group(0)

        # Compute new relative path from current file location
        new_rel = os.path.relpath(new_abs, file_dir)
        changed = True
        return f"{prefix}{new_rel}{suffix}"

    # Match markdown links: [text](path) and ![alt](path)
    new_content = re.sub(
        r'(!?\[[^\]]*\]\()([^)]+)(\))',
        replace_link,
        content,
    )

    if changed:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

    return changed


def fix_all_links(path_mapping):
    """Fix links in all .md files under output/."""
    fixed = 0
    total = 0

    for root, dirs, files in os.walk(OUTPUT):
        for f in files:
            if not f.endswith(".md"):
                continue
            total += 1
            filepath = os.path.join(root, f)
            if fix_links_in_file(filepath, path_mapping):
                fixed += 1

            if total % 5000 == 0:
                print(f"  Processed {total} files, {fixed} updated...")

    return total, fixed


def main():
    print("=" * 60)
    print("GfG Notes Reorganizer")
    print("=" * 60)

    if not os.path.isdir(OLD_ROOT):
        print(f"ERROR: {OLD_ROOT} not found")
        return

    # Safety: count all files before
    before_md = sum(1 for _, _, fs in os.walk(OUTPUT) for f in fs if f.endswith(".md"))
    before_img = sum(1 for _, _, fs in os.walk(os.path.join(OUTPUT, "src")) for f in fs)
    before_total = sum(1 for _, _, fs in os.walk(OUTPUT) for _ in fs)
    print(f"\n  BEFORE: {before_md} .md files, {before_img} images, {before_total} total files")

    # Step 1: Build path mapping BEFORE moving
    print("\n[1/4] Building path mapping...")
    path_mapping = build_path_mapping()
    print(f"  {len(path_mapping)} paths mapped")

    # Step 2: Move folders
    print("\n[2/4] Moving folders...")
    move_folders()

    # Step 3: Safety check — count files after move
    print("\n[3/4] Verifying no files lost...")
    after_md = sum(1 for _, _, fs in os.walk(OUTPUT) for f in fs if f.endswith(".md"))
    after_img = sum(1 for _, _, fs in os.walk(os.path.join(OUTPUT, "src")) for f in fs)
    after_total = sum(1 for _, _, fs in os.walk(OUTPUT) for _ in fs)
    print(f"  AFTER:  {after_md} .md files, {after_img} images, {after_total} total files")

    if after_md != before_md:
        print(f"  ABORT: .md file count changed! {before_md} -> {after_md}")
        print("  Something went wrong. Investigate before fixing links.")
        return
    if after_total != before_total:
        print(f"  ABORT: total file count changed! {before_total} -> {after_total}")
        print("  Something went wrong. Investigate before fixing links.")
        return
    print("  OK: all files accounted for")

    # Step 4: Fix links in all .md files
    print("\n[4/4] Fixing links in markdown files...")
    total, fixed = fix_all_links(path_mapping)
    print(f"  Done: {fixed}/{total} files updated")

    # Cleanup: remove old root if empty
    remaining = os.listdir(OLD_ROOT) if os.path.isdir(OLD_ROOT) else []
    if not remaining:
        os.rmdir(OLD_ROOT)
        print(f"\n  Removed empty directory: {OLD_ROOT}")
    else:
        print(f"\n  Remaining in old root: {remaining}")

    print("\nReorganization complete!")


if __name__ == "__main__":
    main()
