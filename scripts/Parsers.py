from typing import Tuple
import onnx_graphsurgeon as gs
from Deeploy.Targets.Generic.Parsers import SoftmaxParser
from Deeploy.DeeployTypes import NetworkContext


class ISoftmaxParser(SoftmaxParser):

    def __init__(self):
        super().__init__()

    def parseNode(self, node: gs.Node) -> bool:
        wellFormed = super().parseNode(node)

        if wellFormed:
            wellFormed = all([
                'coeffA' in node.attrs,
                'coeffB' in node.attrs,
                'coeffC' in node.attrs,
                'log2' in node.attrs,
            ])

        if wellFormed:
            self.operatorRepresentation['coeffA'] = int(node.attrs['coeffA'].values)
            self.operatorRepresentation['coeffB'] = int(node.attrs['coeffB'].values)
            self.operatorRepresentation['coeffC'] = int(node.attrs['coeffC'].values)
            self.operatorRepresentation['log2'] = int(node.attrs['log2'].values)
            self.operatorRepresentation['n_levels'] = int(node.attrs['n_levels'].values)

        return wellFormed

    def parseNodeCtxt(self,
                      ctxt: NetworkContext,
                      node: gs.Node,
                      channels_first: bool = True) -> Tuple[NetworkContext, bool]:

        newCtxt, ret = super().parseNodeCtxt(ctxt, node, channels_first)

        return newCtxt, ret
