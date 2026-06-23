from setuptools import setup, find_packages

setup(
    name='ckanext-banten-theme',
    version='1.0.0',
    description='SATU DATA Banten — gov-formal CKAN theme for the Banten provincial open-data portal',
    author='Pemprov Banten',
    license='AGPL',
    packages=find_packages(exclude=['tests']),
    namespace_packages=['ckanext'],
    include_package_data=True,
    package_data={
        'ckanext.banten_theme': [
            'templates/**/*.html',
            'public/banten/**/*',
        ],
    },
    entry_points={
        'ckan.plugins': [
            'banten_theme = ckanext.banten_theme.plugin:BantenThemePlugin',
        ],
    },
)
