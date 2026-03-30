#!/usr/bin/env python3
"""Reorganize v4 - Create DSA and System Design buckets."""

import os
import re
import shutil

OUTPUT = "output"

MOVES = [
    # === 13_DSA (Data Structures and Algorithms) ===
    # Main DSA folder from Programming_Languages
    ("10_Programming_Languages/DSA", "13_DSA"),
    # Logic building (closely related to DSA practice)
    ("10_Programming_Languages/Logic_Building", "13_DSA/Logic_Building"),

    # === 14_System_Design ===
    # OOP Design Patterns (30 files - creational, structural, behavioral, UML)
    ("08_Software_Engineering/Software_Engineering/61_oops_object_oriented_design", "14_System_Design/Design_Patterns"),
    # Software Design Principles
    ("08_Software_Engineering/Software_Engineering/59_principles_of_software_design", "14_System_Design/Design_Principles"),
    # Distributed Systems (361 files - core system design topic)
    ("02_Systems_and_Architecture/Distributed_Systems", "14_System_Design/Distributed_Systems"),
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
            print(f"  SKIP (not found): {src_rel}")
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
            if total % 5000 == 0:
                print(f"  Scanned {total} files, {fixed} updated...")
    return total, fixed


def main():
    print("=" * 60)
    print("GfG Notes Reorganizer v4 - DSA & System Design buckets")
    print("=" * 60)
    before_total, before_md = count_files(OUTPUT)
    print(f"\n  BEFORE: {before_md} .md, {before_total} total")

    print("\n[1/4] Building path mapping...")
    path_mapping = build_path_mapping()
    print(f"  {len(path_mapping)} paths mapped")

    print("\n[2/4] Moving subfolders...")
    moved = do_moves()
    print(f"  {moved} folders moved")

    print("\n[3/4] Verifying no files lost...")
    after_total, after_md = count_files(OUTPUT)
    print(f"  AFTER:  {after_md} .md, {after_total} total")
    if after_md != before_md or after_total != before_total:
        print(f"  ABORT: count mismatch!")
        return
    print("  OK: all files accounted for")

    print("\n[4/4] Fixing links...")
    total, fixed = fix_links(path_mapping)
    print(f"  Done: {fixed}/{total} files updated")
    print("\nReorganization v4 complete!")


if __name__ == "__main__":
    main()
