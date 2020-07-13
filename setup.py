import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="isitsnowinginberlin",
    version="2.0.0",
    author="Jeremy Mayeres",
    author_email="jeremy@jerr.dev",
    description="Is it snowing in Berlin?",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jerr0328/isitsnowinginberlin",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.7",
    install_requires=["aiocache[redis]", "fastapi[all]", "fastapi_camelcase", "httpx"],
)
