"""
File: backup_manager.py
Description: Backup and restore management for file translations
Author: Arjun Li
Created: 2026-04-15
Last Modified: 2026-04-15
Related modules: models.py, whole_file_translator.py
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from src.models import BackupRecord


def create_backup(
    backup_dir: Path,
    root: Path,
    files: list[Path],
) -> BackupRecord:
    """Create timestamped backup of files.

    Args:
        backup_dir: Root backup directory
        root: Project root path
        files: Files to backup

    Returns:
        BackupRecord with backup details
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_path = backup_dir / timestamp

    if not backup_path.exists():
        backup_path.mkdir(parents=True)

    backed_up: list[Path] = []
    for file in files:
        if not file.exists():
            continue
        rel_path = file.relative_to(root)
        dest = backup_path / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, dest)
        backed_up.append(file)

    record = BackupRecord(
        backup_id=timestamp,
        backup_path=backup_path,
        files_backed_up=backed_up,
    )
    record_file = backup_path / "backup_record.json"
    record_file.write_text(
        record.to_dict().__repr__(),
        encoding="utf-8",
    )

    latest_dir = backup_dir / "latest"
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    shutil.copytree(backup_path, latest_dir)

    return record


def restore_backup(
    backup_dir: Path,
    root: Path,
    backup_id: str | None = None,
    specific_file: str | None = None,
) -> list[Path]:
    """Restore files from backup.

    Args:
        backup_dir: Root backup directory
        root: Project root path
        backup_id: Backup ID to restore (None = latest)
        specific_file: Specific file to restore (None = all)

    Returns:
        List of restored files
    """
    if backup_id:
        backup_path = backup_dir / backup_id
    else:
        backup_path = backup_dir / "latest"

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")

    restored: list[Path] = []

    if specific_file:
        src = backup_path / specific_file
        dest = root / specific_file
        if src.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            restored.append(dest)
    else:
        for src in backup_path.glob("**/*"):
            if src.is_file() and src.name != "backup_record.json":
                rel_path = src.relative_to(backup_path)
                dest = root / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                restored.append(dest)

    return restored


def list_backups(backup_dir: Path) -> list[BackupRecord]:
    """List all available backups with detailed file info."""
    backups: list[BackupRecord] = []

    if not backup_dir.exists():
        return backups

    for entry in backup_dir.iterdir():
        if entry.is_dir() and entry.name != "latest":
            # Try to read backup_record.json if exists
            record_file = entry / "backup_record.json"
            files_backed_up: list[Path] = []

            if record_file.exists():
                data = eval(record_file.read_text(encoding="utf-8"))
                files_backed_up = [Path(f) for f in data.get("files", [])]
            else:
                # Backup without record file - scan files manually
                for f in entry.glob("**/*"):
                    if f.is_file():
                        files_backed_up.append(f.relative_to(entry))

            # Parse timestamp from backup_id (format: YYYYMMDD_HHMMSS)
            backup_id = entry.name
            try:
                created_at = datetime.strptime(backup_id, "%Y%m%d_%H%M%S")
            except ValueError:
                created_at = datetime.now()

            backups.append(
                BackupRecord(
                    backup_id=backup_id,
                    backup_path=entry,
                    files_backed_up=files_backed_up,
                    created_at=created_at,
                    total_files=len(files_backed_up),
                )
            )

    return sorted(backups, key=lambda b: b.backup_id, reverse=True)


def cleanup_backups(
    backup_dir: Path,
    keep_count: int = 2,
) -> list[str]:
    """Clean up old backups, keeping only recent ones.

    Args:
        backup_dir: Root backup directory
        keep_count: Number of backups to keep

    Returns:
        List of removed backup IDs
    """
    backups = list_backups(backup_dir)
    removed: list[str] = []

    for backup in backups[keep_count:]:
        shutil.rmtree(backup.backup_path)
        removed.append(backup.backup_id)

    return removed


def get_backup_size(backup_dir: Path) -> int:
    """Get total size of backup directory in bytes."""
    if not backup_dir.exists():
        return 0
    total = 0
    for f in backup_dir.glob("**/*"):
        if f.is_file():
            total += f.stat().st_size
    return total
