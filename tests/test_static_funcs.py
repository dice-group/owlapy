from unittest.mock import call, patch

from owlapy.static_funcs import download_external_files, move, stopJVM


def test_move_changes_module_of_class():
    class Dummy:
        pass

    Dummy.__module__ = "some.other.module"
    move(Dummy)
    assert Dummy.__module__ == __name__


def test_move_multiple_classes():
    class A:
        pass

    class B:
        pass

    move(A, B)
    assert A.__module__ == __name__
    assert B.__module__ == __name__


def test_download_external_files_skips_when_already_extracted():
    with patch("owlapy.static_funcs.os.path.exists", return_value=True) as mock_exists, \
         patch("owlapy.static_funcs.subprocess.run") as mock_run, \
         patch("owlapy.static_funcs.shutil.move") as mock_shutil_move, \
         patch("owlapy.static_funcs.os.remove") as mock_remove:
        download_external_files("ftp://example.com/files/KGs.zip")

        mock_exists.assert_called_once()
        mock_run.assert_not_called()
        mock_shutil_move.assert_not_called()
        mock_remove.assert_not_called()


def test_download_external_files_downloads_and_extracts_on_linux():
    with patch("owlapy.static_funcs.os.path.exists", return_value=False), \
         patch("owlapy.static_funcs.subprocess.run") as mock_run, \
         patch("owlapy.static_funcs.platform.system", return_value="Linux"), \
         patch("owlapy.static_funcs.shutil.move") as mock_shutil_move, \
         patch("owlapy.static_funcs.os.remove") as mock_remove:
        download_external_files("ftp://example.com/files/KGs.zip")

        assert mock_run.call_args_list == [
            call(['curl', '-O', 'ftp://example.com/files/KGs.zip']),
            call(['unzip', 'KGs.zip']),
        ]
        mock_remove.assert_called_once()
        mock_shutil_move.assert_called_once()


def test_download_external_files_extracts_with_tar_on_windows():
    with patch("owlapy.static_funcs.os.path.exists", return_value=False), \
         patch("owlapy.static_funcs.subprocess.run") as mock_run, \
         patch("owlapy.static_funcs.platform.system", return_value="Windows"), \
         patch("owlapy.static_funcs.shutil.move"), \
         patch("owlapy.static_funcs.os.remove"):
        download_external_files("ftp://example.com/files/KGs.zip")

        assert mock_run.call_args_list == [
            call(['curl', '-O', 'ftp://example.com/files/KGs.zip']),
            call(['tar', '-xf', 'KGs.zip']),
        ]


def test_stop_jvm_is_noop_when_not_started():
    with patch("owlapy.static_funcs.jpype.isJVMStarted", return_value=False), \
         patch("owlapy.static_funcs.jpype.detachThreadFromJVM") as mock_detach, \
         patch("owlapy.static_funcs.jpype.shutdownJVM") as mock_shutdown:
        stopJVM()

        mock_detach.assert_not_called()
        mock_shutdown.assert_not_called()


def test_stop_jvm_detaches_and_shuts_down_when_started():
    # Real JVM start/stop is intentionally avoided here: jpype does not support
    # restarting a JVM once shut down within the same process, which would break
    # every JVM-backed test that runs later in the same pytest session.
    with patch("owlapy.static_funcs.jpype.isJVMStarted", return_value=True), \
         patch("owlapy.static_funcs.jpype.detachThreadFromJVM") as mock_detach, \
         patch("owlapy.static_funcs.jpype.shutdownJVM") as mock_shutdown:
        stopJVM()

        mock_detach.assert_called_once()
        mock_shutdown.assert_called_once()
