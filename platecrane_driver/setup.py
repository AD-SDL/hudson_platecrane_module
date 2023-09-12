from setuptools import setup, find_packages

package_name = 'platecrane_driver'
install_requires = ['pyusb']

setup(
    name='platecrane_driver',
    version='0.0.2',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=install_requires,
    zip_safe=True,
    python_requires=">=3.8",
    maintainer='Rafael Vescovi, Abe Stoka and Doga Ozgulbas',
    maintainer_email='ravescovi@anl.gov',
    description='Driver for the Platecrane and Sciclops',
    url='https://github.com/AD-SDL/platecrane_driver.git',
    license='MIT License',
    entry_points={'console_scripts': [
             'platecrane_driver = platecrane_driver.platecrane_driver:main_null',
             'sciclops_driver = platecrane_driver.sciclops_driver:main_null',
        ]},
)
