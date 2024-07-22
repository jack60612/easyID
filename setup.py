from setuptools import setup

dependencies = [
    "packaging",
    "compreface-sdk~=0.6.0",
    "requests~=2.29.0",
    "opencv-python~=4.10.0.84",
    "numpy~=1.26.4",
    "PySide6~=6.7.2",
    "PySide6-Addons~=6.7.2",
    "PySide6-Essentials~=6.7.2",
]

dev_dependencies = [
    "flake8",
    "mypy",
    "types-pyyaml",
    "types-setuptools",
    "black",
    "isort",
    "pre-commit",
    "pylint",
]


setup(
    name="easyID",
    packages=["easyID", "easyID.classes", "easyID.threads", "easyID.threads.exporters", "scripts"],
    entry_points={
        "console_scripts": ["easyID = easyID.easyID:main"],
    },
    url="https://github.com/jack60612/easyID",
    license="",
    author="Jack Nelson",
    author_email="jack@jacknelson.xyz",
    setup_requires=["setuptools_scm"],
    install_requires=dependencies,
    extras_require=dict(
        dev=dev_dependencies,
    ),
    description="EasyID Client",
)
