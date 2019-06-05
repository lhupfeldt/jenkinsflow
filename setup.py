import sys, os

from setuptools import setup
from setuptools.command.test import test as TestCommand


PROJECT_ROOT, _ = os.path.split(__file__)
PROJECT_NAME = 'jenkinsflow'
COPYRIGHT = u"Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT"
PROJECT_AUTHORS = u"Lars Hupfeldt Nielsen"
PROJECT_EMAILS = 'lhn@hupfeldtit.dk'
PROJECT_URL = "https://github.com/lhupfeldt/jenkinsflow"
SHORT_DESCRIPTION = 'Python API with high level build flow constructs (parallel/serial) for Jenkins (and Hudson).'
LONG_DESCRIPTION = open(os.path.join(PROJECT_ROOT, "README.rst")).read()

on_rtd = os.environ.get('READTHEDOCS') == 'True'
is_ci = os.environ.get('CI', 'false').lower() == 'true'


_here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_here, 'py_version_check.py')) as ff:
    exec(ff.read())


class Test(TestCommand):
    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import test.run
        if is_ci:
            print("Running under CI")
            # Note 'mock' is also hardcoded in .travis.yml
            sys.exit(test.run.cli(apis='mock,script', mock_speedup=10))
        sys.exit(test.run.cli(apis='mock,script'))


flow_requires = ['atomicfile>=1.0,<=2.0']
cli_requires = ['click>=6.0']
job_load_requires = ['tenjin>=1.1.1']
jenkins_api_requires = ['requests>=2.20,<=3.0']
# You need to install python(3)-devel to be be able to install psutil, see INSTALL.md
script_api_requires = ['psutil>=5.2.2', 'setproctitle>=1.1.10']
visual_requires = ['bottle>=0.12.1']

if not on_rtd:
    install_requires = flow_requires + cli_requires + job_load_requires + jenkins_api_requires + script_api_requires + visual_requires
else:
    install_requires = flow_requires + cli_requires + jenkins_api_requires + script_api_requires

tests_require = [
    'pytest>=4.4.0', 'pytest-cov>=2.4.0', 'pytest-instafail>=0.3.0', 'pytest-xdist>=1.16',
    'click>=6.0', 'tenjin>=1.1.1', 'bottle>=0.12',
    # The test also tests creation of the documentation
    'sphinx>=1.6.1', 'sphinxcontrib-programoutput']

tests_require.append('objproxies>=0.9.4')

extras = {
    'test': tests_require,
}

if __name__ == "__main__":
    setup(
        name=PROJECT_NAME.lower(),
        version_command=('git describe', 'pep440-git'),
        author=PROJECT_AUTHORS,
        author_email=PROJECT_EMAILS,
        packages=['jenkinsflow', 'jenkinsflow.utils', 'jenkinsflow.cli'],
        package_dir={'jenkinsflow':'.', 'jenkinsflow.utils': 'utils', 'jenkinsflow.cli': 'cli'},
        zip_safe=True,
        include_package_data=False,
        python_requires='>=3.6.0',
        install_requires=install_requires,
        setup_requires='setuptools-version-command>=2.2',
        test_suite='test',
        tests_require=tests_require,
        extras_require=extras,
        cmdclass={'test': Test},
        url=PROJECT_URL,
        description=SHORT_DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        long_description_content_type='text/x-rst',
        license='BSD',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            # 'Programming Language :: Python :: 3.8',
            'Topic :: Software Development :: Testing',
        ],
        entry_points='''
            [console_scripts]
            jenkinsflow=jenkinsflow.cli.cli:cli
        ''',
    )
