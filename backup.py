#!/usr/bin/env python3
"""
backup.py — Create a backup of the Cabinet-Office system.
Copies all essential files from ~/.hermes to ~/.hermes-backup.

What gets backed up:
  - /shared/agent-registry.md (cluster-wide single source of truth)
  - Top-level registry.json
  - Per-profile: SOUL.md, profile.yaml, config.yaml
  - Per-profile skills/*/SKILL.md
  - System contracts (system/*.md, system/*.json)
  - System scripts (system/scripts/*.py)
  - Ledger (system/ledger/**/*.json)

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

    # 1. Shared cluster-wide files
    shared_dir = os.path.join(SOURCE_BASE, "shared")
    if os.path.exists(shared_dir):
        for f in os.listdir(shared_dir):
            if f.endswith(('.md', '.json')):
                files.append(f"shared/{f}")

    # 2. Top-level registry.json
    top_registry = os.path.join(SOURCE_BASE, "registry.json")
    if os.path.exists(top_registry):
        files.append("registry.json")

    # 3. Per-profile files
    profiles_dir = os.path.join(SOURCE_BASE, "profiles")
    if os.path.exists(profiles_dir):
        for folder in sorted(os.listdir(profiles_dir)):
            if folder.startswith('.'):
                continue
            profile_dir = os.path.join(profiles_dir, folder)
            if not os.path.isdir(profile_dir):
                continue

            # Profile-level files
            for fname in ["SOUL.md", "profile.yaml", "config.yaml"]:
                fpath = os.path.join(profile_dir, fname)
                if os.path.exists(fpath):
                    files.append(f"profiles/{folder}/{fname}")

            # Skills (any SKILL.md under skills/)
            skills_dir = os.path.join(profile_dir, "skills")
            if os.path.exists(skills_dir):
                for root, dirs, filenames in os.walk(skills_dir):
                    for f in filenames:
                        if f.endswith('.md'):
                            full_path = os.path.join(root, f)
                            rel_path = os.path.relpath(full_path, SOURCE_BASE)
                            files.append(rel_path)

    # 4. System contracts
    system_dir = os.path.join(SOURCE_BASE, "system")
    if os.path.exists(system_dir):
        for f in os.listdir(system_dir):
            if f.endswith(('.md', '.json', '.yaml', '.yml')):
                files.append(f"system/{f}")

    # 5. System scripts
    scripts_dir = os.path.join(SOURCE_BASE, "system/scripts")
    if os.path.exists(scripts_dir):
        for f in os.listdir(scripts_dir):
            if f.endswith('.py'):
                files.append(f"system/scripts/{f}")

    # 6. Ledger directory (JSON only)
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
