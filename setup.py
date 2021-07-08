from setuptools import setup

VERSION = "0.0.1"
with open("README.md") as f:
    readme = f.read()

setup(
    name="flask-rest-serializer",
    version=VERSION,
    description="Make it easy to serialize flask api request and response",
    long_description=readme,
    long_description_content_type='text/markdown',
    url="https://github.com/panjianjun/flask_rest_serializer",
    author="bayi",
    author_email="bayipan@gmail.com",
    license="Apache Software License",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    keywords="flask rest serializer automatically swagger",
    packages=["flask_rest_serializer"],
    install_requires=["flask", "marshmallow", "apispec", "pyyaml"],
)
