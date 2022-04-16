import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="saymore2rdf-sylvainloiseau",
    author_email="sylvain.loiseau@univ-paris13.fr",
    author="Sylvain Loiseau",
    version="0.1.0",
    description="Modeling fieldwork metadata with RDF",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.univ-paris13.fr/sylvain.loiseau/rdf4corpusmetadata",
    project_urls={
        "Bug Tracker": "https://gitlab.univ-paris13.fr/sylvain.loiseau/rdf4corpusmetadata",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)

