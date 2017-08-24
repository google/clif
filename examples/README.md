This dir contains various examples on how to use CLIF to wrap typical code.
See detailed explanation in [CLIF Python Primer](../clif/python/primer.md).

Some examples depend on each other, so we create a virtualenv to install
resulting Python extension modules.

To build all examples run

```
virtualenv /tmp/examples
cmake -DPYCLIF=../bin/pyclif .

make callbacks
cd callbacks
/tmp/examples/bin/pip install .
cd python
/tmp/examples/bin/python callbacks_test
cd ../..

make inheritance
cd inheritance
/tmp/examples/bin/pip install .
cd python
/tmp/examples/bin/python inheritance_test
cd ../..

make property
cd property
/tmp/examples/bin/pip install .
cd python
/tmp/examples/bin/python property_test
cd ../..

make templates
cd templates
/tmp/examples/bin/pip install .
cd python
/tmp/examples/bin/python templates_test
cd ../..

# The example "wrapfunc" depends on the example "wrappod" (see below). Hence,
# install "wrappod" before installing "wrapfunc".
make wrapfunc
cd wrapfunc
/tmp/examples/bin/pip install .
cd python
/tmp/examples/bin/python wrapfunc_test
cd ../..

make wrapmethod
cd wrapmethod
/tmp/examples/bin/pip install .
cd python
/tmp/examples/bin/python wrapmethod_test
cd ../..

make wrappod
cd wrappod
/tmp/examples/bin/pip install .
cd python
/tmp/examples/bin/python wrappod_test
cd ../..
```
