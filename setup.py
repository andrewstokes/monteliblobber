
from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    lic = f.read()

setup(
    name='Monteliblobber',
    version='1.0',
    packages=find_packages(exclude='tests'),
    url='https://github.com/andrewstokes/monteliblobber',
    license=lic,
    author='Andrew Stokes',
    author_email='andrewstokes@users.noreply.github.com',
    description='A reasonable way to extract and contextualize network artifacts from blobs.',
    long_description=readme,
)
