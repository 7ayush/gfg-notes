#!/usr/bin/env python3
"""Reorganize v5 - Final cleanup of deep misplacements."""

import os
import re
import shutil

OUTPUT = "output"

MOVES = [
    # TypeScript tutorial (105 files) stuck inside macOS/framework -> Web_Technology
    ("11_Productivity_Tools/macOS/03_what_is_a_framework/04_typescript_tutorial", "09_Web_Technology/Web_Technology/TypeScript"),
    # Flutter tutorial (104 files) stuck inside macOS/framework -> Programming_Languages
    ("11_Productivity_Tools/macOS/03_what_is_a_framework/05_flutter_tutorial", "10_Programming_Languages/Flutter"),
    # AngularJS (315 files) stuck inside Cyber_Security/Web_Security -> Web_Technology
    ("03_Networking_and_Security/Cyber_Security/Web_Security/19_angularjs", "09_Web_Technology/Web_Technology/AngularJS"),
    # ExpressJS (206 files) stuck inside Cyber_Security/Web_Security -> Web_Technology
    ("03_Networking_and_Security/Cyber_Security/Web_Security/18_express_js", "09_Web_Technology/Web_Technology/ExpressJS"),
    # DSA interview questions (552 files) stuck inside Engineering_Math/quiz -> DSA
    ("01_Computer_Science_Foundations/Engineering_Mathematics/89_quiz_corner_gq/148_commonly_asked_data_structure_interview_questions_set_1", "13_DSA/Interview_Questions"),
    # Digital Electronics (185 files) stuck inside Mathematics_for_CS/number_system -> CS_Foundations
    ("01_Computer_Science_Foundations/Mathematics_for_CS/02_number_system_and_base_conversions/01_digital_electronics_logic_design_tutorials", "02_Systems_and_Architecture/Computer_Organization/Digital_Electronics"),
    # Docker tutorial (73 files) stuck inside Linux/top_command -> Web_Technology or Software_Engineering
    ("03_Networking_and_Security/Linux/56_top_command_in_linux_with_examples/02_docker_tutorial", "08_Software_Engineering/Software_Engineering/Docker"),
    # Google Cloud Platform (178 files) stuck inside Linux/ifconfig -> Networking
    ("03_Networking_and_Security/Linux/41_ifconfig_command_in_linux_with_examples/04_google_cloud_platform_tutorial", "03_Networking_and_Security/Computer_Networks/Google_Cloud_Platform"),
    # Spring Boot (139 files) stuck inside Web_Technology/Web_Server -> Web_Technology top level
    ("09_Web_Technology/Web_Technology/Web_Server/05_spring_boot", "09_Web_Technology/Web_Technology/Spring_Boot"),
]


def count_files(base):
    total = md = 0
    for _, _, files in os.walk(base):
        total += len(files)
        md += sum(1 for f in files if f.endswith(".md"))
    return total, md


def build_path_mapping():
    mapping = {}
    for src_rel, dst_rel in MOVES:
        old_dir = os.path.join(OUTPUT, src_rel)
        new_dir = os.path.join(OUTPUT, dst_rel)
        if not os.path.isdir(old_dir):
            continue
        mapping[old_dir] = new_dir
        old_md = old_dir + ".md"
        new_md = new_dir + ".md"
        if os.path.isfile(old_md):
            mapping[old_md] = new_md
        for root, dirs, files in os.walk(old_dir):
            rel = os.path.relpath(root, old_dir)
            new_root = os.path.join(new_dir, rel) if rel != "." else new_dir
            for f in files:
                mapping[os.path.join(root, f)] = os.path.join(new_root, f)
    return mapping


def do_moves():
    moved = 0
    for src_rel, dst_rel in MOVES:
        old_dir = os.path.join(OUTPUT, src_rel)
        new_dir = os.path.join(OUTPUT, dst_rel)
        if not os.path.isdir(old_dir):
            print(f"  SKIP: {src_rel}")
            continue
        os.makedirs(os.path.dirname(new_dir), exist_ok=True)
        shutil.move(old_dir, new_dir)
        moved += 1
        old_md = old_dir + ".md"
        new_md = new_dir + ".md"
        if os.path.isfile(old_md):
            os.makedirs(os.path.dirname(new_md), exist_ok=True)
            shutil.move(old_md, new_md)
        print(f"  [{moved}] {src_rel} -> {dst_rel}")
    return moved


def fix_links(path_mapping):
    fixed = total = 0
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
                prefix, rel_path, suffix = match.group(1), match.group(2), match.group(3)
                old_abs = os.path.normpath(os.path.join(file_dir, rel_path))
                new_abs = path_mapping.get(old_abs)
                if new_abs is None:
                    return match.group(0)
                changed = True
                return f"{prefix}{os.path.relpath(new_abs, file_dir)}{suffix}"
            new_content = re.sub(r'(!?\[[^\]]*\]\()([^)]+)(\))', replace_link, content)
            if changed:
                with open(filepath, "w", encoding="utf-8") as fh:
                    fh.write(new_content)
                fixed += 1
            if total % 10000 == 0:
                print(f"  Scanned {total} files, {fixed} updated...")
    return total, fixed


def main():
    print("=" * 60)
    print("GfG Notes Reorganizer v5 - Final deep cleanup")
    print("=" * 60)
    before_total, before_md = count_files(OUTPUT)
    print(f"\n  BEFORE: {before_md} .md, {before_total} total")
    print("\n[1/4] Building path mapping...")
    path_mapping = build_path_mapping()
    print(f"  {len(path_mapping)} paths mapped")
    print("\n[2/4] Moving subfolders...")
    moved = do_moves()
    print(f"  {moved} folders moved")
    print("\n[3/4] Verifying...")
    after_total, after_md = count_files(OUTPUT)
    print(f"  AFTER:  {after_md} .md, {after_total} total")
    if after_md != before_md or after_total != before_total:
        print(f"  ABORT: count mismatch!")
        return
    print("  OK")
    print("\n[4/4] Fixing links...")
    total, fixed = fix_links(path_mapping)
    print(f"  Done: {fixed}/{total} files updated")
    print("\nv5 complete!")


if __name__ == "__main__":
    main()
