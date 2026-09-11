#!/usr/bin/env python3
"""
backup.py — Create a backup of the Cabinet-Office system.
Copies all essential files from ~/.hermes to ~/.hermes-backup.

Usage:
    python3 backup.py    # create backup
"""
import os
import shutil
from datetime import datetime


BACKUP_BASE = "/home/massi/.hermes-backup"
SOURCE_BASE = "/home/massi/.hermes"


def get_backup_files():
    """Get list of files to backup"""
    files = []

    # System contracts
    system_dir = os.path.join(SOURCE_BASE, "system")
    for f in os.listdir(system_dir):
        if f.endswith(('.md', '.json', '.yaml', '.yml')):
            files.append(f"system/{f}")

    # System scripts
    scripts_dir = os.path.join(SOURCE_BASE, "system/scripts")
    for f in os.listdir(scripts_dir):
        if f.endswith('.py'):
            files.append(f"system/scripts/{f}")

    # Profile SOUL.md and profile.yaml
    profiles_dir = os.path.join(SOURCE_BASE, "profiles")
    for folder in os.listdir(profiles_dir):
        if folder.startswith('.'):
            continue
        profile_dir = os.path.join(profiles_dir, folder)
        if os.path.isdir(profile_dir):
            soul = os.path.join(profile_dir, "SOUL.md")
            profile = os.path.join(profile_dir, "profile.yaml")
            if os.path.exists(soul):
                files.append(f"profiles/{folder}/SOUL.md")
            if os.path.exists(profile):
                files.append(f"profiles/{folder}/profile.yaml")

    # Ledger directory (JSON only)
    ledger_dir = os.path.join(SOURCE_BASE, "system/ledger")
    if os.path.exists(ledger_dir):
        for root, dirs, filenames in os.walk(ledger_dir):
            for f in filenames:
                if f.endswith('.json'):
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, SOURCE_BASE)
                    files.append(rel_path)

    return sorted(files)


def main():
    print("=" * 60)
    print("BACKUP — Cabinet-Office System")
    print("=" * 60)
    print(f"Source: {SOURCE_BASE}")
    print(f"Target: {BACKUP_BASE}")
    print(f"Date:   {datetime.now().isoformat()}")
    print()

    files = get_backup_files()
    print(f"Files to backup: {len(files)}")

    # Create backup directory
    os.makedirs(BACKUP_BASE, exist_ok=True)

    # Copy files
    copied = 0
    for rel_path in files:
        src = os.path.join(SOURCE_BASE, rel_path)
        dst = os.path.join(BACKUP_BASE, rel_path)

        os.makedirs(os.path.dirname(dst), exist_ok=True)

        if os.path.exists(src):
            shutil.copy2(src, dst)
            copied += 1
        else:
            print(f"  ✗ Missing: {rel_path}")

    print(f"\n✓ Backed up {copied} files to {BACKUP_BASE}")
    print(f"\nTo restore, run:")
    print(f"  python3 {BACKUP_BASE}/restore.py")


if __name__ == "__main__":
    main()
