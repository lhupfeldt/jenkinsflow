from setuptools import setup
import os

PROJECT_ROOT, _ = os.path.split(__file__)
REVISION = '0.1.1'
PROJECT_NAME = 'jenkinsflow'
PROJECT_AUTHORS = "Lars Hupfeldt Nielsen"
PROJECT_EMAILS = 'lhn@hupfeldtit.dk'
PROJECT_URL = "https://github.com/lhupfeldt/jenkinsflow"
SHORT_DESCRIPTION = 'Python API with high level build flow constructs (parallel/serial) for Jenkins (and Hudson).'

try:
    DESCRIPTION = open(os.path.join(PROJECT_ROOT, "README.md")).read()
except IOError:
    DESCRIPTION = SHORT_DESCRIPTION

setup(
    name=PROJECT_NAME.lower(),
    version=REVISION,
    author=PROJECT_AUTHORS,
    author_email=PROJECT_EMAILS,
    packages=['jenkinsflow'],
    package_dir={'jenkinsflow':'.'},
    zip_safe=True,
    include_package_data=False,
    install_requires=['restkit', 'jenkinsapi', 'enum34', 'tenjin', 'bottle', 'atomicfile', 'proxytypes'],
    test_suite='pytest',
    tests_require=['pytest', 'pytest-cov', 'pytest-cache', 'pytest-instafail', 'pytest-xdist', 'logilab-devtools', 'proxytypes'],
    url=PROJECT_URL,
    description=SHORT_DESCRIPTION,
    long_description=DESCRIPTION,
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Testing',
    ],
)
