from typing import Dict, NamedTuple, Type
import onnx
import onnx_graphsurgeon as gs
from Deeploy.AbstractDataTypes import BaseType, PointerClass
from Deeploy.CommonExtensions.DataTypes import int8_t

class NetworkInfo(NamedTuple):
    dir: str
    inputTypes: Dict[str, Type[BaseType]]

    def onnx_path(self) -> str:
        return f"{self.dir}/network.onnx"

    def test_inputs_path(self) -> str:
        return f"{self.dir}/test_inputs.npz"

    def test_outputs_path(self) -> str:
        return f"{self.dir}/test_outputs.npz"

    def graph(self) -> gs.Graph:
        return gs.import_onnx(onnx.load(self.onnx_path()))


linear = NetworkInfo(
        dir="../networks/linear",
        inputTypes = { "input_0": PointerClass(int8_t) }
)
