from Templates import pulpISoftmaxTemplate
from Deeploy.AbstractDataTypes import PointerClass
from Deeploy.CommonExtensions.DataTypes import int8_t, uint8_t
from Deeploy.DeeployTypes import NodeBinding
from Deeploy.Targets.PULPOpen.Bindings import ForkTransformer
from Deeploy.Targets.Generic.TypeCheckers import SoftmaxChecker


iSoftmaxBindings = [
    NodeBinding(SoftmaxChecker([PointerClass(_type)], [PointerClass(uint8_t)]), pulpISoftmaxTemplate,
                ForkTransformer) for _type in [int8_t, uint8_t]
]
