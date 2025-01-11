from setuptools import setup, find_packages

# Load the README for the long description
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="automate-linkedin",  # Replace with your package name
    version="1.0.0",
    author="Shantanu Parab",  # Replace with your name
    author_email="shantanuparab99@gmail.com",  # Replace with your email
    description="Automate LinkedIn job search and applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shantanuparabumd/automate-linkedin",  # Replace with your GitHub repo URL
    packages=find_packages(),  # Automatically finds all sub-packages
    include_package_data=True,  # Includes files from MANIFEST.in
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "selenium",
        "webdriver-manager",
        "PyYAML",
        "hydra-core",
        "pandas",
    ],
    entry_points={
        "console_scripts": [
            "linkedin-job-automation=automate_linkedin.automate:main",
        ],
    },
)
