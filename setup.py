from setuptools import find_packages, setup

with open("README.rst", "r") as fh:
    long_description = fh.read()

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest"]


setup(
    name="agm",
    version="0.1.3",
    license="Apache",
    author="Alex Wennerberg",
    author_email="alex@alexwennerberg.com",
    description="An (unofficial) command line interface for Google APIs",
    long_description=long_description,
    url="https://github.com/Cloudbakers/agm",
    install_requires=[
        "requests",
        "requests-cache",
        "google-api-python-client",
        "tqdm",
        "colorful",
        "oauth2client",
    ],
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    include_package_data=True,
    entry_points={"console_scripts": ["agm=agm.agm:cli"]},
    python_requires=">=3.5",
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        "License :: OSI Approved :: Apache Software License",
    ],
    keywords=["google google-apis gcp gsuite cli"],
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    project_urls={
        "Documentation": "https://agm.readthedocs.io",
        # 'Say Thanks!': 'http://saythanks.io/to/example',
        "Source": "https://github.com/Cloudbakers/agm/",
        "Tracker": "https://github.com/Cloudbakers/agm/issues",
    },
)
