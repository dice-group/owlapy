"""Tests for the extra-classpath support of owlapy.static_funcs.startJVM (#299)."""
import os
from unittest import mock

from owlapy import static_funcs
from owlapy.static_funcs import EXTRA_CLASSPATH_ENV, _collect_jars, startJVM


def _started_classpath(**kwargs):
    with mock.patch.object(static_funcs.jpype, "startJVM") as start:
        startJVM(**kwargs)
    return start.call_args.kwargs["classpath"]


def test_collect_jars_expands_directories_and_keeps_files(tmp_path):
    (tmp_path / "b.jar").touch()
    (tmp_path / "a.jar").touch()
    (tmp_path / "notes.txt").touch()
    single = str(tmp_path / "single.jar")
    assert _collect_jars([str(tmp_path), single]) == [str(tmp_path / "a.jar"), str(tmp_path / "b.jar"), single]


def test_start_jvm_without_extras_uses_bundled_jars_only(monkeypatch):
    monkeypatch.delenv(EXTRA_CLASSPATH_ENV, raising=False)
    classpath = _started_classpath()
    assert classpath and all(os.path.basename(j).endswith(".jar") for j in classpath)


def test_start_jvm_appends_env_and_argument_jars_after_bundled(monkeypatch, tmp_path):
    monkeypatch.delenv(EXTRA_CLASSPATH_ENV, raising=False)
    bundled = _started_classpath()

    (tmp_path / "from_dir.jar").touch()
    env_single = str(tmp_path / "env_single.jar")
    arg_single = str(tmp_path / "arg_single.jar")
    monkeypatch.setenv(EXTRA_CLASSPATH_ENV, os.pathsep.join([str(tmp_path), env_single, ""]))

    classpath = _started_classpath(extra_jars=[arg_single])
    assert classpath[:len(bundled)] == bundled
    assert classpath[len(bundled):] == [arg_single, str(tmp_path / "from_dir.jar"), env_single]
