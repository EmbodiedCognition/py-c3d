import setuptools

setuptools.setup(
    name='lmj.c3d',
    version='0.1',
    install_requires=['numpy'],
    namespace_packages=['lmj'],
    py_modules=['lmj.c3d'],
    scripts=['c3d_viewer.py'],
    author='Leif Johnson',
    author_email='leif@leifjohnson.net',
    description='A library for reading and writing C3D binary files',
    long_description=open('README.rst').read(),
    license='MIT',
    keywords=('c3d '
              'motion-tracking'),
    url='http://github.com/lmjohns3/py-c3d',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        ],
    )
