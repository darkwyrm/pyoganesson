from setuptools import setup, find_packages

setup(
	name='pyoganesson',
	version='0.1',
	description='Pure Python implementation of the Oganesson messaging framework',
	url='https://github.com/darkwyrm/pyoganesson',
	author='Jon Yoder',
	author_email='jon@yoder.cloud',
	license='MIT',
	packages=find_packages(),
	classifiers=[
		"Development Status :: 2 - Pre-Alpha",
		"Intended Audience :: Developers",
		"Topic :: Communications",
		"Programming Language :: Python :: 3.5",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
	python_requires='>=3.5',
	install_requires=[
		'PyNaCl>=1.3.0',
		'pycryptostring>=1.0.0'
	]
)
