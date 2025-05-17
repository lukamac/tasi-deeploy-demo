# 1. setup deployer
# 2. generate code and necessary files (hex)
# 3. (optional) generate test and simulate

# Simplifications:
# - fixed platform, deployer, tiling, network

import os
from Util import format_c_file
from Deployer import setup_deployer
from NetworkInfo import linear, iSoftmax


deployer = setup_deployer(iSoftmax)

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
