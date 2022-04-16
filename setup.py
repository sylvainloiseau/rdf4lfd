import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rdfFieldData-sylvainloiseau",
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
    install_requires=[
        'rdflib==6.1.1',
        'xmltodict==0.12.0'
    ],
    package_dir={"rdffielddata": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)

