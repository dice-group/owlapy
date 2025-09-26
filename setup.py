from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()
setup(
    name="owlapy",
    description="OWLAPY is a Python Framework for creating and manipulating OWL Ontologies.",
    version="1.6.1",
    packages=find_packages(),
    include_package_data=True,
    package_data={'owlapy': ['jar_dependencies/*.jar'],},
    install_requires=[
        "scikit-learn>=1.5.2",
        "pandas>=1.5.0",
        "requests>=2.32.3",
        "rdflib>=6.0.2",
        "ruff>=0.7.2",
        "parsimonious>=0.8.1",
        "pytest>=8.1.1",
        "sortedcontainers>=2.4.0",
        "owlready2>=0.40",
        "JPype1>=1.5.0",
        "tqdm>=4.66.5",
        "fastapi>=0.115.5",
        "httpx>=0.27.2",
        "uvicorn>=0.32.1",
        "dicee==0.2.0"],
    author='Caglar Demir',
    author_email='caglardemir8@gmail.com',
    url='https://github.com/dice-group/owlapy',
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering"],
    python_requires='>=3.10.13',
    entry_points={"console_scripts": ["owlapy=owlapy.scripts.run:main", "owlapy-serve=owlapy.scripts.owlapy_serve:main"]},
    long_description=long_description,
    long_description_content_type="text/markdown",
)
