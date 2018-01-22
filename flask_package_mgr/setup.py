from setuptools import setup, find_packages

setup(
    name='flask_package_mgr',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'marshmallow'
        ],
    setup_requires=[
        'pytest-runner',
        ],
    test_require=[
        'pytest',
        ],
    )
