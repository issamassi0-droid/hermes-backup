#!/usr/bin/env python3
"""
restore.py — Restore Cabinet-Office system from backup.
Copies all files from ~/.hermes-backup back to ~/.hermes.

Usage:
    python3 restore.py           # restore all files
    python3 restore.py --dry-run # show what would be restored
    python3 restore.py --list    # list backed up files
"""
import os
import shutil
import sys


BACKUP_BASE = "/home/massi/.hermes-backup"
RESTORE_BASE = "/home/massi/.hermes"


def get_backup_files():
    """Get list of all files in backup"""
    files = []
    for root, dirs, filenames in os.walk(BACKUP_BASE):
        dirs[:] = [d for d in dirs if d != '.git']
        for f in filenames:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, BACKUP_BASE)
            files.append(rel_path)
    return sorted(files)


def restore_file(rel_path, dry_run=False):
    """Restore single file from backup"""
    src = os.path.join(BACKUP_BASE, rel_path)
    dst = os.path.join(RESTORE_BASE, rel_path)

    if not os.path.exists(src):
        print(f"Source missing: {rel_path}")
        return False

    if dry_run:
        print(f"  {rel_path}")
        return True

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return True


def main():
    dry_run = "--dry-run" in sys.argv
    list_only = "--list" in sys.argv

    if not os.path.exists(BACKUP_BASE):
        print(f"Backup not found: {BACKUP_BASE}")
        sys.exit(1)

    files = get_backup_files()

    if list_only:
        print(f"Backup Files ({len(files)})")
        for f in files:
            print(f"  {f}")
        sys.exit(0)

    print("RESTORE — Cabinet-Office System")
    print(f"Source: {BACKUP_BASE}")
    print(f"Target: {RESTORE_BASE}")
    print(f"Files:  {len(files)}")
    print(f"Mode:   {'DRY RUN' if dry_run else 'RESTORE'}")
    print()

    restored = 0
    failed = 0

    for rel_path in files:
        if restore_file(rel_path, dry_run=dry_run):
            restored += 1
        else:
            failed += 1

    print()
    if dry_run:
        print(f"DRY RUN: {restored} files would be restored")
    else:
        print(f"RESTORED: {restored} files, {failed} failed")


if __name__ == "__main__":
    main()
