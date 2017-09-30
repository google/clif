This dir contains various examples on how to use CLIF to wrap typical code.
See detailed explanation in [CLIF Python Primer](../clif/python/primer.md).

Some examples depend on each other, so we create a virtualenv to install
resulting Python extension modules.

To build all examples run

```
virtualenv /tmp/examples
cmake -DPYCLIF=${PWD}/../bin/pyclif  -DPYCLIF_PROTO=${PWD}/../bin/pyclif_proto .

make callbacks
cd callbacks
/tmp/examples/bin/pip install .
cd python
/tmp/examples/bin/python callbacks_test.py
cd ../..

make inheritance
make base
make python_inheritance
make hidden_base
make operation
cd inheritance
/tmp/examples/bin/pip install .
cd python
/tmp/examples/bin/python inheritance_test.py
/tmp/examples/bin/python hidden_base_test.py
/tmp/examples/bin/python operation_test.py
cd ../..

make myoptions
cd property
/tmp/examples/bin/pip install .
cd python
/tmp/examples/bin/python myoptions_test.py
cd ../..

make templates
cd templates
/tmp/examples/bin/pip install .
cd python
/tmp/examples/bin/python templates_test.py
cd ../..

# The example "wrapfunc" depends on the example "wrappod" (see below). Hence,
# install "wrappod" before installing "wrapfunc".
make wrapfunc
cd wrapfunc
/tmp/examples/bin/pip install .
cd python
/tmp/examples/bin/python wrapfunc_test.py
cd ../..

make wrapmethod
cd wrapmethod
/tmp/examples/bin/pip install .
cd python
/tmp/examples/bin/python wrapmethod_test.py
cd ../..

make wrappod
cd wrappod
/tmp/examples/bin/pip install .
cd python
/tmp/examples/bin/python wrappod_test.py
cd ../..

make wrap_protos
# Install the proto module and wrapper before installing the example module.
cd wrap_protos/protos
/tmp/examples/bin/pip install .
cd ..
/tmp/examples/bin/pip install .
cd python
/tmp/examples/bin/python wrap_protos_test.py
cd ../..
```
