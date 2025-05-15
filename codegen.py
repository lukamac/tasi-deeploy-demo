# 1. setup deployer
# 2. generate code and necessary files (hex)
# 3. (optional) generate test and simulate

# Simplifications:
# - fixed platform, deployer, tiling, network

from Deeploy.CommonExtensions.DataTypes import int8_t
from ortools.constraint_solver.pywrapcp import IntVar
from typing import List, OrderedDict, Union
from Deeploy.DeeployTypes import ConstantBuffer, NetworkContext, ONNXLayer, PointerClass, SubGraph, TransientBuffer
from Deeploy.MemoryLevelExtension.NetworkDeployers.MemoryLevelDeployer import MemoryDeployerWrapper
from Deeploy.TilingExtension.TilerExtension import Tiler, TilerDeployerWrapper
from Deeploy.TilingExtension.TilerModel import TilerModel
import onnx_graphsurgeon as gs
import onnx
import Deeploy.Targets.Neureka.Platform as Neureka
from Deeploy.MemoryLevelExtension.MemoryLevels import MemoryHierarchy, MemoryLevel
from Deeploy.Targets.Neureka.Deployer import NeurekaDeployer
from Deeploy.EngineExtension.NetworkDeployers.EngineColoringDeployer import EngineColoringDeployerWrapper
from Deeploy.MemoryLevelExtension.OptimizationPasses.MemoryLevelAnnotationPasses import AnnotateIOMemoryLevel, AnnotateDefaultMemoryLevel, AnnotateNeurekaWeightMemoryLevel


L3 = MemoryLevel(name = "L3", neighbourNames = ["L2"], size = 64000000)
L2 = MemoryLevel(name = "L2", neighbourNames = ["L3", "L1"], size = 512000)
L1 = MemoryLevel(name = "L1", neighbourNames = ["L2"], size = 128000)
WMEM = MemoryLevel(name = "WeightMemory_SRAM", neighbourNames = [], size = 4 * 1024 * 1024)

memoryHierarchy = MemoryHierarchy([L3, L2, L1, WMEM])
memoryHierarchy.setDefaultMemoryLevel("L2")

platform = Neureka.MemoryNeurekaPlatform(
    memoryHierarchy,
    defaultTargetMemoryLevel=L1,
    weightMemoryLevel=WMEM,
)

def scheduler(graph: gs.Graph):
    return graph.nodes

graph = gs.import_onnx(onnx.load("network.onnx"))

inputTypes = { "input_0": PointerClass(int8_t) }

loweringOptimizer = Neureka.NeurekaOptimizer

deployer = NeurekaDeployer(
    graph,
    platform,
    inputTypes,
    loweringOptimizer,
    scheduler,
    "DeeployNetwork",
    default_channels_first=False,
    deeployStateDir="deeployState",
)

# Make the deployer engine-color-aware
deployer = EngineColoringDeployerWrapper(deployer)

memoryLevelAnnotationPasses = [
    AnnotateIOMemoryLevel("L3"),
    AnnotateDefaultMemoryLevel(memoryHierarchy),
    AnnotateNeurekaWeightMemoryLevel(neurekaEngineName=platform.engines[0].name,
                                     weightMemoryLevel=WMEM)
]

deployer = MemoryDeployerWrapper(deployer, memoryLevelAnnotationPasses)

class MyTiler(Tiler):

    def multiBufferStrategy(self, tilerModel: TilerModel, ctxt: NetworkContext, pattern: SubGraph, path: List[str],
                            hop: str, tensorName: str) -> Union[int, IntVar]:
        buffer = ctxt.lookup(tensorName)

        if hop == "L1" or isinstance(buffer, TransientBuffer):
            return 1
        else:
            return 2

deployer = TilerDeployerWrapper(deployer, MyTiler)

# Tiler defaults
deployer.tiler.visualizeMemoryAlloc = False
deployer.tiler.memoryAllocStrategy = "TetrisRandom"
deployer.tiler.searchStrategy = "random-max"

# User provided input types and offsets
# Offsets are important only for sign prop platforms, which is not the case for the pulp-platform
# Sign prop platforms are platforms that only implement unsigned kernels and use offsets to implement signed operations
inputOffsets = { "input_0": 0 }

def _mockScheduler(graph: gs.Graph) -> List[List[gs.Node]]:
    schedule = [[node] for node in graph.nodes]
    return schedule

def _filterSchedule(schedule: List[List[gs.Node]], layerBinding: OrderedDict[str, ONNXLayer]) -> List[List[gs.Node]]:
    filteredSchedule = []
    for pattern in schedule:
        filteredSchedulePattern = []
        for node in pattern:
            if node.name in layerBinding.keys():
                filteredSchedulePattern.append(node)
        filteredSchedule.append(filteredSchedulePattern)
    return filteredSchedule

schedule = _filterSchedule(_mockScheduler(graph), deployer.layerBinding)

_ = deployer.generateFunction()
