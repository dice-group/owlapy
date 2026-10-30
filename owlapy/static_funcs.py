"""Static functions for general purposes."""
import importlib.resources as resources
import os
import platform
import shutil
import subprocess
from typing import Iterable, Optional

import jpype
import jpype.imports

# NOTE: Static functions closely related with owl classes should be placed in utils.py
# or util_owl_static_funcs.py not here


def move(*args):
    """"Move" an imported class to the current module by setting the classes __module__ attribute.

    This is useful for documentation purposes to hide internal packages in sphinx.

    Args:
        args: List of classes to move.
    """
    from inspect import currentframe
    f = currentframe()
    f = f.f_back
    mod = f.f_globals['__name__']
    for cls in args:
        cls.__module__ = mod


def download_external_files(ftp_link: str):

    file_name = ftp_link.split("/")[-1]
    root_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
    current_dir = os.path.join(os.getcwd(), file_name[:-4])
    if not os.path.exists(os.path.join(root_dir, file_name[:-4])):
        subprocess.run(['curl', '-O', ftp_link])

        if platform.system() == "Windows":
            subprocess.run(['tar', '-xf', file_name])
        else:
            subprocess.run(['unzip', file_name])
        os.remove(os.path.join(os.getcwd(), file_name))
        shutil.move(current_dir, root_dir)


EXTRA_CLASSPATH_ENV = "OWLAPY_EXTRA_CLASSPATH"


def _collect_jars(entries) -> list:
    """Expand classpath entries into jar paths: a directory contributes the ``.jar`` files directly inside it
    (sorted, for a deterministic classpath), anything else is taken as a path to a single jar."""
    jars = []
    for entry in entries:
        entry = os.path.expanduser(str(entry))
        if os.path.isdir(entry):
            jars.extend(sorted(os.path.join(entry, f) for f in os.listdir(entry) if f.endswith('.jar')))
        else:
            jars.append(entry)
    return jars


def startJVM(extra_jars: Optional[Iterable[str]] = None):
    """Start the JVM with jar dependencies. This method is called automatically on object initialization,
    if the JVM is not started yet.

    JPype cannot extend the classpath once the JVM is running, so third-party packages building on owlapy
    (e.g. ones needing an additional Java library) must register their jars before the first ontology or
    reasoner is created. There are two ways to do so:

    - the ``OWLAPY_EXTRA_CLASSPATH`` environment variable: ``os.pathsep``-separated jar files and/or
      directories (every ``.jar`` directly inside a directory is added);
    - the ``extra_jars`` argument, with the same kind of entries, by calling ``startJVM(extra_jars=...)``
      explicitly before anything else starts the JVM.

    Extra jars are appended after the bundled ones, so the bundled OWLAPI version takes precedence on
    conflicting classes.

    Args:
        extra_jars: Additional jar files and/or directories containing jars to put on the classpath.
    """

    # Access the jar_dependencies folder inside the 'owlapy' package
    with resources.path('owlapy', 'jar_dependencies') as jar_folder_path:
        jar_files = _collect_jars([str(jar_folder_path)])

    extra_entries = list(extra_jars or [])
    extra_entries += [e for e in os.environ.get(EXTRA_CLASSPATH_ENV, "").split(os.pathsep) if e]

    # Start JVM with the found jar files
    jpype.startJVM(classpath=jar_files + _collect_jars(extra_entries))


def stopJVM() -> None:
    """Detaches the thread from Java packages and shuts down the java virtual machine hosted by jpype."""
    if jpype.isJVMStarted():
        jpype.detachThreadFromJVM()
        jpype.shutdownJVM()
