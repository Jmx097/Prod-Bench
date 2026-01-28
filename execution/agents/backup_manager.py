#!/usr/bin/env python3
"""
Backup Manager Agent - Handles pre-processing backups and cleanup.

Features:
- Creates timestamped backups before processing
- Enforces retention policy (deletes old backups)
- Provides restore functionality
- Stub for Cloud Upload
"""

import shutil
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
import time # For stub

from .base_agent import BaseAgent


class BackupManagerAgent(BaseAgent):
    """
    Manages file backups with retention policy.
    
    Config keys:
        enabled: Enable backup creation (default: True)
        backup_dir: Directory for backups (default: .backups)
        retention_days: Days to keep backups (default: 7)
        upload_to_drive: Enable cloud upload stub (default: False)
    """
    
    def _get_backup_dir(self, output_dir: Path) -> Path:
        """Get or create backup directory."""
        backup_dirname = self.config.get("backup_dir", ".backups")
        backup_dir = output_dir / backup_dirname
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir
    
    def _generate_backup_name(self, original_path: Path) -> str:
        """Generate timestamped backup filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{original_path.stem}_{timestamp}{original_path.suffix}"
    
    def _cleanup_old_backups(self, backup_dir: Path) -> int:
        """Remove backups older than retention period."""
        retention_days = self.config.get("retention_days", 7)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        cleaned_count = 0
        
        for backup_file in backup_dir.iterdir():
            if not backup_file.is_file():
                continue
            
            # Check file modification time
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            if mtime < cutoff_date:
                try:
                    backup_file.unlink()
                    cleaned_count += 1
                    self.logger.debug(f"Removed old backup: {backup_file.name}")
                except Exception as e:
                    self.logger.warning(f"Could not remove {backup_file.name}: {e}")
        
        return cleaned_count
    
    def _list_backups(self, backup_dir: Path) -> List[Dict[str, Any]]:
        """List all backups with metadata."""
        backups = []
        
        for backup_file in sorted(backup_dir.iterdir()):
            if not backup_file.is_file():
                continue
            
            stat = backup_file.stat()
            backups.append({
                "path": str(backup_file),
                "name": backup_file.name,
                "size_bytes": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return backups
    
    def _stub_cloud_upload(self, file_path: Path) -> str:
        """Stub for Google Drive upload."""
        self.logger.info(f"[STUB] Uploading {file_path.name} to Google Drive...")
        # Simulate latency
        # time.sleep(0.5) 
        return "mock_success_id_12345"

    def _execute(self, input_path: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Create structured backup and optionally upload to cloud (stub).
        
        Returns:
            {
                "backup_path": str - Path to backup file (or None if disabled),
                "backup_enabled": bool - Whether backup was created,
                "cleaned_count": int - Number of old backups removed,
                "total_backups": int - Current backup count,
                "cloud_upload": str - Status of cloud upload
            }
        """
        self.validate_input(input_path)
        
        enabled = self.config.get("enabled", True)
        
        if not enabled:
            self.logger.info("Backup is disabled")
            return {
                "backup_path": None,
                "backup_enabled": False,
                "cleaned_count": 0,
                "total_backups": 0
            }
        
        backup_dir = self._get_backup_dir(output_dir)
        
        # Create backup
        backup_name = self._generate_backup_name(input_path)
        backup_path = backup_dir / backup_name
        
        self.logger.info(f"Creating backup: {backup_name}")
        shutil.copy2(input_path, backup_path)
        
        if not backup_path.exists():
            raise RuntimeError(f"Failed to create backup: {backup_path}")
        
        # Cleanup old backups
        cleaned_count = self._cleanup_old_backups(backup_dir)
        if cleaned_count > 0:
            self.logger.info(f"Cleaned {cleaned_count} old backup(s)")
        
        # Cloud Upload Stub
        cloud_status = "skipped"
        if self.config.get("upload_to_drive"):
            cloud_status = self._stub_cloud_upload(backup_path)
        
        # Count total backups
        total_backups = len(self._list_backups(backup_dir))
        
        self.logger.info(f"Backup created successfully")
        
        return {
            "backup_path": str(backup_path),
            "backup_enabled": True,
            "cleaned_count": cleaned_count,
            "total_backups": total_backups,
            "cloud_upload": cloud_status
        }
    
    def restore(self, backup_path: str, restore_to: str) -> Dict[str, Any]:
        """
        Restore a file from backup.
        """
        backup = Path(backup_path)
        destination = Path(restore_to)
        
        if not backup.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")
        
        shutil.copy2(backup, destination)
        
        return {
            "restored": True,
            "restore_path": str(destination)
        }
