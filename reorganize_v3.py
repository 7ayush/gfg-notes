#!/usr/bin/env python3
"""Reorganize output/ subfolders v3 - fix remaining misplacements."""

import os
import re
import shutil

OUTPUT = "output"

MOVES = [
    # JS frameworks -> Web_Technology
    ("10_Programming_Languages/JavaScript/132_react", "09_Web_Technology/Web_Technology/React"),
    ("10_Programming_Languages/JavaScript/134_lodash", "09_Web_Technology/Web_Technology/Lodash"),
    ("10_Programming_Languages/JavaScript/142_vue_js", "09_Web_Technology/Web_Technology/Vue"),
    ("10_Programming_Languages/JavaScript/143_angular_tutorial", "09_Web_Technology/Web_Technology/Angular"),
    ("10_Programming_Languages/JavaScript/144_nextjs_tutorial", "09_Web_Technology/Web_Technology/NextJS"),
    ("10_Programming_Languages/JavaScript/145_nuxtjs", "09_Web_Technology/Web_Technology/NuxtJS"),
    # Python web frameworks -> Web_Technology
    ("10_Programming_Languages/Python/70_python_introduction_to_web_development_using_flask", "09_Web_Technology/Web_Technology/Flask_Intro"),
    ("10_Programming_Languages/Python/71_python_web_development_django", "09_Web_Technology/Web_Technology/Django"),
    ("10_Programming_Languages/Python/79_python_web_development", "09_Web_Technology/Web_Technology/Python_Web_Dev"),
    ("10_Programming_Languages/Python/89_flask_tutorial", "09_Web_Technology/Web_Technology/Flask"),
    ("10_Programming_Languages/Python/90_django_tutorial", "09_Web_Technology/Web_Technology/Django_Tutorial"),
    # Python data science libs -> Data_Science
    ("10_Programming_Languages/Python/83_pandas_tutorial", "07_Data_Science_and_Analytics/Data_Science_with_Python/Pandas_Tutorial"),
    ("10_Programming_Languages/Python/84_matplotlib_tutorial", "07_Data_Science_and_Analytics/Data_Science_with_Python/Matplotlib_Tutorial"),
    ("10_Programming_Languages/Python/85_python_seaborn_tutorial", "07_Data_Science_and_Analytics/Data_Science_with_Python/Seaborn_Tutorial"),
    # ML/DL libs -> AI_and_ML
    ("10_Programming_Languages/Python/86_scikit_learn_tutorial", "06_AI_and_Machine_Learning/Machine_Learning/Scikit_Learn_Tutorial"),
    ("10_Programming_Languages/Python/87_lightgbm_light_gradient_boosting_machine", "06_AI_and_Machine_Learning/Machine_Learning/LightGBM"),
    ("10_Programming_Languages/Python/88_keras_tutorial", "06_AI_and_Machine_Learning/Deep_Learning/Keras_Tutorial"),
    ("10_Programming_Languages/Python/67_introduction_to_tensorflow", "06_AI_and_Machine_Learning/Deep_Learning/TensorFlow_Intro"),
    ("10_Programming_Languages/Python/68_what_is_keras", "06_AI_and_Machine_Learning/Deep_Learning/Keras_Intro"),
    ("10_Programming_Languages/Python/69_getting_started_with_pytorch", "06_AI_and_Machine_Learning/Deep_Learning/PyTorch_Intro"),
    # Python MongoDB -> Databases
    ("10_Programming_Languages/Python/82_python_mongodb_tutorial", "05_Databases/DBMS/Python_MongoDB"),
    # Android from Dropbox -> Programming_Languages
    ("11_Productivity_Tools/Dropbox/01_android_tutorial", "10_Programming_Languages/Android"),
    # Advanced Java interviews -> Software_Engineering
    ("10_Programming_Languages/Java/170_advanced_java_interview_questions", "08_Software_Engineering/Software_Engineering/Advanced_Java_Interview"),
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
    print("GfG Notes Reorganizer v3")
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
    print("\nReorganization v3 complete!")


if __name__ == "__main__":
    main()
