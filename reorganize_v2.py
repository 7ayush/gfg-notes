#!/usr/bin/env python3
"""Reorganize output/ subfolders into correct buckets and fix all links.

Safety: counts all files before and after moves, aborts if any are lost.
"""

import os
import re
import shutil

OUTPUT = "output"

# (source_relative_to_output, dest_relative_to_output)
MOVES = [
    # Programming Languages from Computer_Fundamentals
    ("01_Computer_Science_Foundations/Computer_Fundamentals/46_c_programming_language", "10_Programming_Languages/C"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/47_c_plus_plus", "10_Programming_Languages/CPP"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/48_csharp_programming_language", "10_Programming_Languages/CSharp"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/49_java", "10_Programming_Languages/Java"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/50_python_programming_language_tutorial", "10_Programming_Languages/Python"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/51_javascript_tutorial", "10_Programming_Languages/JavaScript"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/52_logic_building_problems", "10_Programming_Languages/Logic_Building"),
    # Web topics from Computer_Fundamentals -> Web_Technology
    ("01_Computer_Science_Foundations/Computer_Fundamentals/12_web_browser", "09_Web_Technology/Web_Technology/Web_Browser"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/13_web_server_and_its_type", "09_Web_Technology/Web_Technology/Web_Server"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/14_web_protocols", "09_Web_Technology/Web_Technology/Web_Protocols"),
    # Web Security -> Cyber_Security
    ("01_Computer_Science_Foundations/Computer_Fundamentals/15_web_security_considerations", "03_Networking_and_Security/Cyber_Security/Web_Security"),
    # Productivity Tools from Computer_Fundamentals
    ("01_Computer_Science_Foundations/Computer_Fundamentals/08_windows_10_tutorial", "11_Productivity_Tools/Windows"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/10_what_is_macos", "11_Productivity_Tools/macOS"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/19_ms_word_tutorial", "11_Productivity_Tools/MS_Word"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/20_google_docs_tutorial_for_beginners_to_advance", "11_Productivity_Tools/Google_Docs"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/21_excel_tutorial", "11_Productivity_Tools/Excel"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/22_google_sheets_tutorial", "11_Productivity_Tools/Google_Sheets"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/26_gmail_tutorial", "11_Productivity_Tools/Gmail"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/29_dropbox_an_introduction", "11_Productivity_Tools/Dropbox"),
    # Networking from Computer_Fundamentals -> Computer_Networks
    ("01_Computer_Science_Foundations/Computer_Fundamentals/53_basics_computer_networking", "03_Networking_and_Security/Computer_Networks/Basics_Networking"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/54_types_of_area_networks_lan_man_and_wan", "03_Networking_and_Security/Computer_Networks/Area_Networks"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/55_types_of_network_topology", "03_Networking_and_Security/Computer_Networks/Network_Topology"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/18_what_is_wi_fiwireless_fidelity", "03_Networking_and_Security/Computer_Networks/WiFi"),
    ("01_Computer_Science_Foundations/Computer_Fundamentals/61_access_control_in_computer_network", "03_Networking_and_Security/Computer_Networks/Access_Control"),
    # Malware -> Cyber_Security
    ("01_Computer_Science_Foundations/Computer_Fundamentals/59_malware_and_its_types", "03_Networking_and_Security/Cyber_Security/Malware"),
    # DSA from Mathematics_for_CS -> Programming_Languages
    ("01_Computer_Science_Foundations/Mathematics_for_CS/35_dsa_tutorial_learn_data_structures_and_algorithms", "10_Programming_Languages/DSA"),
    # Computer Graphics -> standalone
    ("01_Computer_Science_Foundations/Mathematics_for_CS/36_introduction_to_computer_graphics", "12_Computer_Graphics"),
    # ML Math -> AI_and_ML
    ("01_Computer_Science_Foundations/Mathematics_for_CS/37_ml_machine_learning", "06_AI_and_Machine_Learning/Machine_Learning/ML_Math_Foundations"),
    # Network from Math -> Computer_Networks
    ("01_Computer_Science_Foundations/Mathematics_for_CS/39_network_and_communication", "03_Networking_and_Security/Computer_Networks/Network_Communication"),
    # Deep Learning from Data_Science_with_Python -> AI_and_ML
    ("07_Data_Science_and_Analytics/Data_Science_with_Python/54_deep_learning_tutorial", "06_AI_and_Machine_Learning/Deep_Learning"),
]


def count_files(base):
    """Count all files under base."""
    total = 0
    md = 0
    for _, _, files in os.walk(base):
        total += len(files)
        md += sum(1 for f in files if f.endswith(".md"))
    return total, md


def build_path_mapping():
    """Build old_abs -> new_abs mapping for every file that will move."""
    mapping = {}
    for src_rel, dst_rel in MOVES:
        old_dir = os.path.join(OUTPUT, src_rel)
        new_dir = os.path.join(OUTPUT, dst_rel)
        if not os.path.isdir(old_dir):
            continue
        mapping[old_dir] = new_dir
        # Also map sibling .md file
        old_md = old_dir + ".md"
        new_md = new_dir + ".md"
        if os.path.isfile(old_md):
            mapping[old_md] = new_md
        # Map all files inside
        for root, dirs, files in os.walk(old_dir):
            rel = os.path.relpath(root, old_dir)
            new_root = os.path.join(new_dir, rel) if rel != "." else new_dir
            for f in files:
                mapping[os.path.join(root, f)] = os.path.join(new_root, f)
    return mapping


def do_moves():
    """Move all folders and their sibling .md files."""
    moved = 0
    for src_rel, dst_rel in MOVES:
        old_dir = os.path.join(OUTPUT, src_rel)
        new_dir = os.path.join(OUTPUT, dst_rel)
        if not os.path.isdir(old_dir):
            print(f"  SKIP (not found): {src_rel}")
            continue
        os.makedirs(os.path.dirname(new_dir), exist_ok=True)
        shutil.move(old_dir, new_dir)
        moved += 1
        # Move sibling .md
        old_md = old_dir + ".md"
        new_md = new_dir + ".md"
        if os.path.isfile(old_md):
            os.makedirs(os.path.dirname(new_md), exist_ok=True)
            shutil.move(old_md, new_md)
        print(f"  [{moved}] {src_rel} -> {dst_rel}")
    return moved


def fix_links(path_mapping):
    """Fix relative links in all .md files."""
    fixed = 0
    total = 0
    for root, dirs, files in os.walk(OUTPUT):
        for f in files:
            if not f.endswith(".md"):
                continue
            total += 1
            filepath = os.path.join(root, f)
            try:
                with open(filepath, "r", encoding="utf-8") as fh:
                    content = fh.read()
            except (UnicodeDecodeError, OSError):
                continue

            file_dir = os.path.dirname(filepath)
            changed = False

            def replace_link(match):
                nonlocal changed
                prefix = match.group(1)
                rel_path = match.group(2)
                suffix = match.group(3)
                old_abs = os.path.normpath(os.path.join(file_dir, rel_path))
                new_abs = path_mapping.get(old_abs)
                if new_abs is None:
                    return match.group(0)
                new_rel = os.path.relpath(new_abs, file_dir)
                changed = True
                return f"{prefix}{new_rel}{suffix}"

            new_content = re.sub(r'(!?\[[^\]]*\]\()([^)]+)(\))', replace_link, content)
            if changed:
                with open(filepath, "w", encoding="utf-8") as fh:
                    fh.write(new_content)
                fixed += 1
            if total % 5000 == 0:
                print(f"  Scanned {total} files, {fixed} updated...")
    return total, fixed


def main():
    print("=" * 60)
    print("GfG Notes Reorganizer v2 - Subfolder Reallocation")
    print("=" * 60)

    # Count before
    before_total, before_md = count_files(OUTPUT)
    print(f"\n  BEFORE: {before_md} .md files, {before_total} total files")

    # Build mapping before moving
    print("\n[1/4] Building path mapping...")
    path_mapping = build_path_mapping()
    print(f"  {len(path_mapping)} paths mapped")

    # Move
    print("\n[2/4] Moving subfolders...")
    moved = do_moves()
    print(f"  {moved} folders moved")

    # Verify
    print("\n[3/4] Verifying no files lost...")
    after_total, after_md = count_files(OUTPUT)
    print(f"  AFTER:  {after_md} .md files, {after_total} total files")
    if after_md != before_md or after_total != before_total:
        print(f"  ABORT: file count mismatch! md: {before_md}->{after_md}, total: {before_total}->{after_total}")
        return
    print("  OK: all files accounted for")

    # Fix links
    print("\n[4/4] Fixing links in markdown files...")
    total, fixed = fix_links(path_mapping)
    print(f"  Done: {fixed}/{total} files updated")

    print("\nReorganization v2 complete!")


if __name__ == "__main__":
    main()
