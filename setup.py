import sys, os

from setuptools import setup


PROJECT_ROOT, _ = os.path.split(__file__)
PROJECT_NAME = 'jenkinsflow'
COPYRIGHT = u"Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT"
PROJECT_AUTHORS = u"Lars Hupfeldt Nielsen"
PROJECT_EMAILS = 'lhn@hupfeldtit.dk'
PROJECT_URL = "https://github.com/lhupfeldt/jenkinsflow"
SHORT_DESCRIPTION = 'Python API with high level build flow constructs (parallel/serial) for Jenkins (and Hudson).'
LONG_DESCRIPTION = open(os.path.join(PROJECT_ROOT, "README.txt")).read()


if sys.version_info.major < 3:
    py_version_requires = ['enum34', 'subprocess32']
    py_version_test_require = ['proxytypes']
else:
    py_version_requires = []
    py_version_test_require = ['objproxies~=0.9.4']


if __name__ == "__main__":
    setup(
        name=PROJECT_NAME.lower(),
        version_command=('git describe', 'pep440-git'),
        author=PROJECT_AUTHORS,
        author_email=PROJECT_EMAILS,
        packages=['jenkinsflow', 'jenkinsflow.cli'],
        package_dir={'jenkinsflow':'.', 'jenkinsflow.cli': 'cli'},
        zip_safe=True,
        include_package_data=False,
        # You need to install python(3)-devel to be be able to install psutil, see INSTALL.md
        install_requires=['requests~=2.7.0',
                          'atomicfile~=1.0',
                          'psutil~=3.2.1',
                          'setproctitle~=1.1.9',
                          'click~=5.1',
                          'tenjin~=1.1.1',
                          'bottle~=0.12.8'] + py_version_requires,
        setup_requires='setuptools-version-command~=2.2',
        test_suite='test',
        test_loader='test.test:TestLoader',
        tests_require=['pytest~=2.8.2', 'pytest-cov~=2.1.0', 'pytest-instafail~=0.3.0', 'pytest-xdist~=1.13.1',
                       'click~=5.1', 'tenjin~=1.1.1', 'bottle~=0.12.8',
                       # The test also tests creation of the documentation
                       'sphinx~=1.3.1', 'sphinxcontrib-programoutput'] + py_version_test_require,
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
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Topic :: Software Development :: Testing',
        ],
        entry_points='''
            [console_scripts]
            jenkinsflow=jenkinsflow.cli.cli:cli
        ''',
    )
