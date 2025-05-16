import onnx
import onnx_graphsurgeon as gs
from Deeploy.DeeployTypes import PointerClass
from Deeploy.CommonExtensions.DataTypes import int8_t

graph = gs.import_onnx(onnx.load("../example_network/network.onnx"))

# User provided input types
inputTypes = { "input_0": PointerClass(int8_t) }
