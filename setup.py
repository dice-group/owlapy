import re

from setuptools import find_packages, setup

_deps = [
    "scikit-learn>=1.5.2",
    "pandas>=1.5.0",
    "requests>=2.32.3",
    "rdflib>=6.0.2",
    "parsimonious>=0.8.1",
    "sortedcontainers>=2.4.0",
    "owlready2>=0.40,<0.51",
    "JPype1>=1.5.0",
    "tqdm>=4.66.5",
    "fastapi>=0.115.5",
    "httpx>=0.27.2",
    "uvicorn>=0.32.1",
    "dicee>=0.3.2,<0.4.0",
    "litserve>=0.2.0",
    "dspy>=3.0.3,<4.0.0",
    "ruff>=0.7.2",
    "pytest>=8.1.1",
]

deps = {b: a for a, b in (re.findall(r"^(([^!=<>~ ]+)(?:[!=<>~ ].*)?$)", x)[0] for x in _deps)}

def deps_list(*pkgs):
    return [deps[pkg] for pkg in pkgs]

extras = dict()
extras["min"] = deps_list(
    "scikit-learn",
    "pandas",
    "requests",
    "rdflib",
    "parsimonious",
    "sortedcontainers",
    "JPype1",
    "tqdm",
    "fastapi",
    "httpx",
    "uvicorn",
    "litserve",
    "dspy",
)

# owlready2 backs only the legacy, owlready2-specific parts of owlapy (`Ontology`,
# `StructuralReasoner`, a few `util_owl_static_funcs` helpers) -- owlapy is migrating away from it
# in favor of the pure-Python RDFLibOntology/RDFLibReasoner (see issue #205), so it's an optional
# extra rather than a hard install-time dependency. `owlapy.owl_ontology`/`owl_reasoner` import
# fine without it; only code paths that actually construct/call owlready2 functionality raise a
# clear ImportError pointing at this extra (see `owlapy/_lazy_owlready2.py`).
extras["owlready2"] = deps_list("owlready2")

extras["dev"] = (extras["min"] + extras["owlready2"] + deps_list("pytest", "ruff"))
extras["agentic"] = (extras["min"] + deps_list("dspy"))
extras["all"] = (extras["dev"] + deps_list("dspy", "dicee"))
install_requires = [extras["min"]]

with open('README.md', 'r') as fh:
    long_description = fh.read()
setup(
    name="owlapy",
    description="OWLAPY is a Python Framework for creating and manipulating OWL Ontologies.",
    version="1.6.6",
    packages=find_packages(),
    include_package_data=True,
    package_data={'owlapy': ['jar_dependencies/*.jar', 'py.typed'],},
    extras_require=extras,
    install_requires=list(install_requires),
    author='Caglar Demir',
    author_email='caglardemir8@gmail.com',
    url='https://github.com/dice-group/owlapy',
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering"],
    python_requires='>=3.11',
    entry_points={"console_scripts": ["owlapy=owlapy.scripts.run:main", "owlapy-serve=owlapy.scripts.owlapy_serve:main"]},
    long_description=long_description,
    long_description_content_type="text/markdown",
)
