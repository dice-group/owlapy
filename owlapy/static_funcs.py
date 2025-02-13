"""Static functions for general purposes."""
import os
import subprocess
import platform
import shutil
import jpype
import jpype.imports
import pkg_resources

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


def startJVM():
    """Start the JVM with jar dependencies. This method is called automatically on object initialization, if the
    JVM is not started yet."""
    # Start a java virtual machine using the dependencies in the respective folder:
    jar_folder = pkg_resources.resource_filename('owlapy', 'jar_dependencies')
    jar_files = [os.path.join(jar_folder, f) for f in os.listdir(jar_folder) if f.endswith('.jar')]
    # Starting JVM
    jpype.startJVM(classpath=jar_files)


def stopJVM() -> None:
    """Detaches the thread from Java packages and shuts down the java virtual machine hosted by jpype."""
    if jpype.isJVMStarted():
        jpype.detachThreadFromJVM()
        jpype.shutdownJVM()
