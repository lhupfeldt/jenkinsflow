import os

from setuptools import setup


PROJECT_ROOT, _ = os.path.split(__file__)
SHORT_VERSION = '0.9'
LONG_VERSION = SHORT_VERSION + '.0'
PROJECT_NAME = 'jenkinsflow'
COPYRIGHT = u"Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT"
PROJECT_AUTHORS = u"Lars Hupfeldt Nielsen"
PROJECT_EMAILS = 'lhn@hupfeldtit.dk'
PROJECT_URL = "https://github.com/lhupfeldt/jenkinsflow"
SHORT_DESCRIPTION = 'Python API with high level build flow constructs (parallel/serial) for Jenkins (and Hudson).'
LONG_DESCRIPTION = open(os.path.join(PROJECT_ROOT, "README.md")).read()

if __name__ == "__main__":
    setup(
        name=PROJECT_NAME.lower(),
        version=LONG_VERSION,
        author=PROJECT_AUTHORS,
        author_email=PROJECT_EMAILS,
        packages=['jenkinsflow', 'jenkinsflow.cli'],
        package_dir={'jenkinsflow':'.', 'jenkinsflow.cli': 'cli'},
        zip_safe=True,
        include_package_data=False,
        install_requires=['restkit', 'enum34', 'tenjin', 'bottle', 'atomicfile', 'subprocess32', 'psutil', 'setproctitle', 'click'],
        test_suite='test',
        test_loader='test.test:TestLoader',
        tests_require=['pytest', 'pytest-cov', 'pytest-cache', 'pytest-instafail', 'pytest-xdist', 'logilab-devtools', 'proxytypes', 'click'],
        url=PROJECT_URL,
        description=SHORT_DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        license='BSD',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 2.7',
            'Topic :: Software Development :: Testing',
        ],
        entry_points='''
            [console_scripts]
            jenkinsflow=jenkinsflow.cli.cli:cli
        ''',
    )
