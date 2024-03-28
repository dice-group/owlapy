from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()
setup(
    name="owlapy",
    description="Owlapy is loosely based on owlapi - the java counterpart, "
                "successfully representing the main owl objects in python.",
    version="0.1.2",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.5.0",
        "rdflib>=6.0.2",
        "parsimonious>=0.8.1",
        "pytest>=8.1.1"],
    author='Caglar Demir',
    author_email='caglardemir8@gmail.com',
    url='https://github.com/dice-group/owlapy',
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Topic :: Scientific/Engineering"],
    python_requires='>=3.10',
    long_description=long_description,
    long_description_content_type="text/markdown",
)
