"""Tests for the extra-classpath support of owlapy.static_funcs.startJVM (#299)."""
import os
from unittest import mock

import pytest

from owlapy import static_funcs
from owlapy.static_funcs import EXTRA_CLASSPATH_ENV, JARS_ENTRY_POINT_GROUP, _collect_jars, startJVM


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


def _install_fake_extension(monkeypatch, site_dir, dist_name, entry_points_txt, module_name=None, module_src=None):
    """Make a fake installed distribution (``*.dist-info`` with entry points) discoverable via ``sys.path``."""
    dist_info = site_dir / f"{dist_name}-0.0.1.dist-info"
    dist_info.mkdir(parents=True)
    (dist_info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {dist_name}\nVersion: 0.0.1\n")
    (dist_info / "entry_points.txt").write_text(entry_points_txt)
    if module_name:
        (site_dir / f"{module_name}.py").write_text(module_src)
    monkeypatch.syspath_prepend(str(site_dir))


def test_start_jvm_discovers_jars_of_installed_extensions(monkeypatch, tmp_path):
    monkeypatch.delenv(EXTRA_CLASSPATH_ENV, raising=False)
    bundled = _started_classpath()

    jar_dir = tmp_path / "jars"
    jar_dir.mkdir()
    (jar_dir / "ext.jar").touch()
    single = str(tmp_path / "single.jar")
    _install_fake_extension(
        monkeypatch, tmp_path / "site", "owlapy-fake-ext",
        f"[{JARS_ENTRY_POINT_GROUP}]\nfake_ext = owlapy_fake_ext:jar_paths\n",
        "owlapy_fake_ext", f"def jar_paths():\n    return [{str(jar_dir)!r}, {single!r}]\n",
    )

    classpath = _started_classpath()
    assert classpath[:len(bundled)] == bundled
    assert classpath[len(bundled):] == [str(jar_dir / "ext.jar"), single]


def test_entry_point_jars_come_after_explicit_ones_without_duplicates(monkeypatch, tmp_path):
    shared = str(tmp_path / "shared.jar")
    own = str(tmp_path / "own.jar")
    env_jar = str(tmp_path / "env.jar")
    monkeypatch.setenv(EXTRA_CLASSPATH_ENV, env_jar)
    with mock.patch.object(static_funcs, "_entry_point_jars", return_value=[shared, own]):
        classpath = _started_classpath(extra_jars=[shared])
    assert classpath[-3:] == [shared, env_jar, own]
    assert classpath.count(shared) == 1


def test_entry_points_are_loaded_in_name_order_and_accept_a_single_path():
    def ep(name, provided):
        entry = mock.Mock(value=f"{name}:jar_paths")
        entry.name = name  # Mock(name=...) would set the mock's repr name instead
        entry.load.return_value = lambda: provided
        return entry

    eps = [ep("zeta", "/z.jar"), ep("alpha", ["/a1.jar", "/a2.jar"])]
    with mock.patch.object(static_funcs, "entry_points", return_value=eps) as found:
        assert static_funcs._entry_point_jars() == ["/a1.jar", "/a2.jar", "/z.jar"]
    found.assert_called_once_with(group=JARS_ENTRY_POINT_GROUP)


def test_broken_entry_point_is_skipped_with_warning(monkeypatch, tmp_path):
    good = str(tmp_path / "good.jar")
    _install_fake_extension(
        monkeypatch, tmp_path / "site", "owlapy-fake-broken",
        f"[{JARS_ENTRY_POINT_GROUP}]\nbroken = owlapy_does_not_exist:jar_paths\n"
        f"good = owlapy_fake_good:jar_paths\n",
        "owlapy_fake_good", f"def jar_paths():\n    return [{good!r}]\n",
    )
    with pytest.warns(RuntimeWarning, match="broken"):
        assert static_funcs._entry_point_jars() == [good]
