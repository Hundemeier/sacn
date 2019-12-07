from setuptools import setup, find_packages

setup(name='sacn',
      version='1.4',
      description='sACN / E1.31 module for easy handling of DMX data over ethernet',
      url='https://www.github.com/Hundemeier/sacn',
      author='Hundemeier',
      author_email='hundemeier99@gmail.com',
      license='MIT License',
      # packages=['sacn', 'sacn.messages', 'sacn.receiving', 'sacn.sending'],
      packages=find_packages(),
      keywords=['sacn e131 e1.31 dmx'],
      python_requires='>=3.6',
      zip_safe=False)
