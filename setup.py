import os

from setuptools import setup


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

with open(os.path.join(_here, 'requirements.txt')) as ff:
    install_requires=[req.strip() for req in  ff.readlines() if req.strip() and req.strip()[0] != "#"]

if __name__ == "__main__":
    setup(
        name=PROJECT_NAME.lower(),
        version_command=('git describe', 'pep440-git'),
        author=PROJECT_AUTHORS,
        author_email=PROJECT_EMAILS,
        packages=[
            'jenkinsflow',
            'jenkinsflow.utils',
            'jenkinsflow.cli',
            'jenkinsflow.demo',
            'jenkinsflow.demo.jobs',
            'jenkinsflow.test',
            'jenkinsflow.test.framework',
            'jenkinsflow.test.framework.cfg',
        ],
        package_dir={
            'jenkinsflow': '.',
            'jenkinsflow.utils': 'utils',
            'jenkinsflow.cli': 'cli',
            'jenkinsflow.demo': 'demo',
            'jenkinsflow.demo.jobs': 'demo/jobs',
            'jenkinsflow.test': 'test',
            'jenkinsflow.test.framework': 'test/framework',
            'jenkinsflow.test.framework.cfg': 'test/framework/cfg',
        },
        zip_safe=True,
        include_package_data=False,
        python_requires='>=3.9.0',
        install_requires=install_requires,
        setup_requires='setuptools-version-command>=2.2',
        test_suite='test',
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
            'Programming Language :: Python :: 3.12',
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.9',
            'Topic :: Software Development :: Testing',
        ],
        entry_points='''
            [console_scripts]
            jenkinsflow=jenkinsflow.cli.cli:cli
        ''',
    )
