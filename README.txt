C++ API
--------
Build Instructions:
1. Install cmake version 3.0 or newer
2. cd share/sdk/cpp_api_examples
3. mkdir build && cd build
4. cmake -DMoco_DIR=/usr/lib/moco/cmake ..
5. make

This should create several executable examples. After connecting MoCo board:
> ./buffer_example
[et al]


C API
--------

Build Instructions:
Install cmake version 3.0 or newer
from the share/sdk/c_api_examples directory run:
> cmake

If you are not running from the MoCo software install directory, specify the root directory as:
> cmake -DMOCO_INSTALL_DIR=<moco_dir>

then run:
> ./c_api_example


Python API
----------
(Note: it is recommended to do this in a virtual environment)

1. Install the package
> pip install /usr/share/moco/sdk/python/moco-*.whl

2. Run example:
> python /usr/share/moco/sdk/python/examples/api_receive.py
