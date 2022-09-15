import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rdf4lfd",
    author_email="sylvain.loiseau@univ-paris13.fr",
    author="Sylvain Loiseau",
    version="0.1.0",
    description="Modeling fieldwork metadata with RDF",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sylvainloiseau/rdfFieldData",
    project_urls={
        "Bug Tracker": "https://github.com/sylvainloiseau/rdfFieldData",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"rdf4lfd": "src"},
    package_data={"rdf4lfd": ["py.typed", 'sample']},
    packages=["rdf4lfd"],
    #packages=setuptools.find_packages(where="src"),
    include_package_data=True,
    install_requires=[
        'rdflib>=6.1.1',
        'xmltodict>=0.12.0',
        'numpy>=1.22.3',
        'pandas>=1.4.2',
        'pandas-ods-reader>=0.1.4'
    ],
    python_requires=">=3.8" ,
    entry_points = {
        'console_scripts': ['rdflfd=rdf4lfd.cli:cli']
    }
)
