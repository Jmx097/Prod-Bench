#!/usr/bin/env python3
"""Unit tests for BackupManagerAgent."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta


class TestBackupManagerAgent:
    """Tests for BackupManagerAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create agent with default config."""
        from execution.agents.backup_manager import BackupManagerAgent
        return BackupManagerAgent({
            "enabled": True,
            "backup_dir": ".backups",
            "retention_days": 7,
        })
    
    @pytest.fixture
    def disabled_agent(self):
        """Create disabled backup agent."""
        from execution.agents.backup_manager import BackupManagerAgent
        return BackupManagerAgent({
            "enabled": False,
            "backup_dir": ".backups",
            "retention_days": 7,
        })
    
    def test_generate_backup_name(self, agent, tmp_path):
        """Test backup filename generation."""
        test_file = tmp_path / "video.mp4"
        name = agent._generate_backup_name(test_file)
        
        assert name.startswith("video_")
        assert name.endswith(".mp4")
        # Should contain timestamp
        assert len(name) > len("video_.mp4")
    
    def test_process_creates_backup(self, agent, tmp_path):
        """Test that backup is created."""
        input_file = tmp_path / "input.mp4"
        input_file.write_bytes(b"test content")
        output_dir = tmp_path / "output"
        
        result = agent.process(str(input_file), str(output_dir))
        
        assert result["success"] is True
        assert result["backup_enabled"] is True
        assert result["backup_path"] is not None
        assert Path(result["backup_path"]).exists()
    
    def test_process_disabled_skips_backup(self, disabled_agent, tmp_path):
        """Test that disabled agent skips backup."""
        input_file = tmp_path / "input.mp4"
        input_file.touch()
        output_dir = tmp_path / "output"
        
        result = disabled_agent.process(str(input_file), str(output_dir))
        
        assert result["backup_path"] is None
    
    def test_cloud_upload_stub(self, agent, tmp_path):
        """Test cloud upload stub."""
        agent.config["upload_to_drive"] = True
        input_file = tmp_path / "test.txt"
        input_file.write_text("content")
        
        # Mock folder setup
        output_dir = tmp_path / "output"
        
        result = agent.process(str(input_file), str(output_dir))
        
        assert result["cloud_upload"] == "mock_success_id_12345"
    
    def test_cleanup_old_backups(self, agent, tmp_path):
        """Test that old backups are cleaned up."""
        backup_dir = tmp_path / ".backups"
        backup_dir.mkdir()
        
        # Create old backup (simulate with file mtime)
        old_backup = backup_dir / "old_backup.mp4"
        old_backup.touch()
        
        # Create recent backup
        new_backup = backup_dir / "new_backup.mp4"
        new_backup.touch()
        
        # Set old backup mtime to 10 days ago
        import os
        old_time = datetime.now() - timedelta(days=10)
        os.utime(old_backup, (old_time.timestamp(), old_time.timestamp()))
        
        cleaned = agent._cleanup_old_backups(backup_dir)
        
        assert cleaned == 1
        assert not old_backup.exists()
        assert new_backup.exists()
    
    def test_restore(self, agent, tmp_path):
        """Test backup restoration."""
        backup_file = tmp_path / "backup.mp4"
        backup_file.write_bytes(b"backup content")
        restore_path = tmp_path / "restored.mp4"
        
        result = agent.restore(str(backup_file), str(restore_path))
        
        assert result["restored"] is True
        assert restore_path.exists()
        assert restore_path.read_bytes() == b"backup content"
