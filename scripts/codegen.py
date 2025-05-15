# 1. setup deployer
# 2. generate code and necessary files (hex)
# 3. (optional) generate test and simulate

# Simplifications:
# - fixed platform, deployer, tiling, network

import os
import shutil
import subprocess
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
from util import format_c_file


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

graph = gs.import_onnx(onnx.load("../example_network/network.onnx"))

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

output_name = "Network"

network_header = f"""
#ifndef __DEEPLOY_{output_name.upper()}__
#define __DEEPLOY_{output_name.upper()}__

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

{deployer.generateIncludeString()}

void RunNetwork(uint32_t core_id, uint32_t numThreads);
void InitNetwork(uint32_t core_id, uint32_t numThread);

{deployer.generateIOBufferInitializationCode()}

#endif  // __DEEPLOY_{output_name.upper()}__
"""

network_implementation = f"""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

{deployer.generateIncludeString()}

#include "Network.h"

{deployer.generateBufferInitializationCode()}

{deployer.generateGlobalDefinitionCode()}

void RunNetwork(__attribute__((unused)) uint32_t core_id, __attribute__((unused)) uint32_t numThreads){{
    {deployer.generateInferenceInitializationCode()}
    {deployer.generateFunction()}
}}

void InitNetwork(__attribute__((unused)) uint32_t core_id, __attribute__((unused)) uint32_t numThreads){{
    {deployer.generateEngineInitializationCode()}
    {deployer.generateBufferAllocationCode()}
}}
"""

gen_dir = "../gen"
gen_inc_dir = f"{gen_dir}/inc"
gen_src_dir = f"{gen_dir}/src"
os.makedirs(gen_inc_dir, exist_ok=True)
os.makedirs(gen_src_dir, exist_ok=True)
network_header_file = f"{gen_inc_dir}/{output_name}.h"
network_implementation_file = f"{gen_src_dir}/{output_name}.c"
with open(network_header_file, "w") as f:
    f.write(network_header)
with open(network_implementation_file, "w") as f:
    f.write(network_implementation)

format_c_file(network_header_file)
format_c_file(network_implementation_file)
