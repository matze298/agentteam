"""Tests the docker functionality."""

from unittest.mock import MagicMock, patch

import pytest

from security.docker import ensure_docker_running


def test_ensure_docker_running() -> None:
    """Tests that ensure_docker_running works as expected."""
    # GIVEN a mocked "docker info" call
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        # WHEN calling ensure_docker_running
        # THEN it should not raise an exception
        ensure_docker_running()


def test_ensure_docker_running_fails_exit_code() -> None:
    """Tests that ensure_docker_running fails when docker info."""
    # GIVEN a mocked "docker info" call that fails
    with patch("subprocess.run", return_value=MagicMock(returncode=1)) as mock_run:
        mock_run.return_value = MagicMock(returncode=1)

        with pytest.raises(SystemExit, match="1"):
            # WHEN calling ensure_docker_running
            # THEN it should exit or raise an error depending on implementation
            ensure_docker_running()
