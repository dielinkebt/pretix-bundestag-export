from setuptools import setup, find_packages

setup(
    name='pretix-bundestag-export',
    version='0.1.0',
    description='CSV- und Excel-Export für Bundestagsveranstaltungen in pretix',
    long_description='Exporter-Plugin für pretix zum Export von Teilnehmerdaten zur Anmeldung beim Deutschen Bundestag.',
    url='https://github.com/dielinkebt/pretix-bundestag-export',
    author='Jannis Hutt',
    author_email='jannis.hutt@dielinkebt.de',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pretix>=2026.1.0',
        'openpyxl>=3.1.0',
    ],
    entry_points="""
[pretix.plugin]
pretix_bundestag_export=pretix_bundestag_export:PretixBundestagExportApp
""",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3.10',
)
