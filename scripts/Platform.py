from Deeploy.MemoryLevelExtension.NetworkDeployers.MemoryLevelDeployer import MemoryDeployerWrapper
from Deeploy.MemoryLevelExtension.MemoryLevels import MemoryHierarchy, MemoryLevel
from Deeploy.Targets.Neureka.Platform import MemoryNeurekaPlatform

L3 = MemoryLevel(name = "L3", neighbourNames = ["L2"], size = 64000000)
L2 = MemoryLevel(name = "L2", neighbourNames = ["L3", "L1"], size = 512000)
#L1 = MemoryLevel(name = "L1", neighbourNames = ["L2"], size = 128000)
L1 = MemoryLevel(name = "L1", neighbourNames = ["L2"], size = 16000)
#WMEM = MemoryLevel(name = "WeightMemory_SRAM", neighbourNames = [], size = 4 * 1024 * 1024)

#memoryHierarchy = MemoryHierarchy([L3, L2, L1, WMEM])
memoryHierarchy = MemoryHierarchy([L3, L2, L1])
memoryHierarchy.setDefaultMemoryLevel("L2")

platform = MemoryNeurekaPlatform(
    memoryHierarchy,
    defaultTargetMemoryLevel=L1,
    #weightMemoryLevel=WMEM,
)

platform.engines[1].includeList.remove("DeeployBasicMath.h")
