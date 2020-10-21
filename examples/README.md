This dir contains various examples on how to use CLIF to wrap typical code.
See detailed explanation in [CLIF Python Primer](../clif/python/primer.md).

Some examples depend on each other, so we create a virtualenv to install
resulting Python extension modules.

To build all examples run

```
# Modify python executable based on location of pyclif.
cmake -DPYTHON_EXECUTABLE=clif-venv/bin/python .

# Compile all CLIF files
make

clif-venv/bin/pip install .
```
