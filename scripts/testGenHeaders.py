from typing import List, Dict, Tuple
from Deeploy.DeeployTypes import ConstantBuffer, NetworkDeployer, VariableBuffer
import numpy as np
import os
from codegen import inputOffsets, inputTypes, deployer
from util import format_c_file


def _shapeBroadcast(ctxt, value, name):
    if ctxt.is_global(f"{name}"):
        broadcastShape = ctxt.lookup(f"{name}").shape
        repeat = np.prod(broadcastShape) / np.prod(value.shape)
        # Raise error if repeat is not an integer
        if repeat % 1 != 0:
            raise ValueError(f"Input {name} has to be broadcastable to shape {broadcastShape}!")
        repeatNum = np.tile(value, int(repeat))
        broadcastNum = repeatNum.reshape(-1)
        ctxt.lookup(f"{name}").shape = broadcastNum.shape
    else:
        broadcastNum = value

    return broadcastNum


def generateTestInputsHeader(deployer: NetworkDeployer, test_inputs: List, inputTypes: Dict, inputOffsets: Dict) -> str:
    retStr = ""
    inputNames = [deployer.ctxt.lookup(buf.name) for buf in deployer.graph.inputs]
    inputTypes = {buf.name: buf._type for buf in inputNames}

    for index, num in enumerate(test_inputs):

        if f"input_{index}" not in inputTypes.keys():
            continue

        # WIESEP: Correctly handle empty arrays
        if np.prod(num.shape) == 0:
            continue

        test_inputs[index] -= inputOffsets[f"input_{index}"]

        broadcastNum = _shapeBroadcast(deployer.ctxt, num, f"input_{index}")

        data_type = inputTypes[f"input_{index}"]
        data_width = inputTypes[f"input_{index}"].referencedType.typeWidth

        retStr += f"{data_type.referencedType.typeName} testInputVector{index}[] ="
        retStr += "{"
        if data_type.referencedType.typeName == 'float32_t':
            list_str = (", ").join([f'{x}f' if not (np.isinf(x) or np.isnan(x)) else str(x) for x in broadcastNum])
        else:
            list_str = (", ").join([str(x) for x in broadcastNum])

        # WIESEP: Arrays have to be 4 byte alinged (at lest in banshee)
        bytes = len(broadcastNum) * (data_width // 8)
        if bytes % 4 != 0:
            bytes = 4 * int((bytes / 4 + 1))
            padding = (bytes * 8) // data_width - len(broadcastNum)
            list_str += ", "
            list_str += (", ").join([str(0) for x in range(padding)])

        retStr += list_str
        retStr += "};\n"

    retStr += f"void* testInputVector[{len(inputTypes)}] = " + "{"
    retStr += ", ".join([
        f"testInputVector{idx}" for idx, _ in enumerate(test_inputs)
        if np.prod(test_inputs[idx].shape) != 0 and f"input_{idx}" in inputTypes.keys()
    ])
    retStr += "};\n"

    return retStr


def generateTestOutputsHeader(deployer: NetworkDeployer,
                              test_outputs: List) -> str:
    output_signed = {}
    output_n_levels = {}
    output_data_type = {}

    retStr = ""

    for index, num in enumerate(test_outputs):
        output_data_type[f"output_{index}"] = deployer.ctxt.lookup(f'output_{index}')._type
        typeName = output_data_type[f"output_{index}"].referencedType.typeName
        typeWidth = output_data_type[f"output_{index}"].referencedType.typeWidth

        retStr += f"#define OUTPUTTYPE {typeName}\n"
        retStr += f"{typeName} testOutputVector{index}[] ="
        retStr += "{"
        list_str = (", ").join([str(x) for x in num.flatten()])
        # WIESEP: Arrays have to be 4 byte alinged (at lest in banshee)
        bytes = len(num) * (typeWidth // 8)
        if bytes % 4 != 0:
            bytes = 4 * int((bytes / 4 + 1))
            padding = (bytes * 8) // typeWidth - len(num)
            list_str += ", "
            list_str += (", ").join([str(0)] * padding)
        retStr += list_str
        retStr += "};\n"

    retStr += f"void* testOutputVector[{len(test_outputs)}] = " + "{"
    retStr += ", ".join([f"testOutputVector{idx}" for idx in range(len(test_outputs))])
    retStr += "};\n"

    return retStr


def generateL3HexDump(deployer: NetworkDeployer, path: str, test_inputs: List, test_outputs: List):

    def type2TypeStr(dataType) -> Tuple[str, int]:
        if dataType.referencedType.typeName == "float32_t":
            retStr = "float32"
            width = 32
        else:
            width = dataType.referencedType.typeWidth
            signed = (dataType.referencedType.typeMin < 0)

            retStr = ""

            if signed:
                retStr += "int"
            else:
                retStr += "uint"

            retStr += str(width)

        return retStr, width

    def dumpBuffer(buf: VariableBuffer, path: str):

        if "input" in buf.name:
            idx = int(buf.name.split("_")[1])
            array = _shapeBroadcast(deployer.ctxt, test_inputs[idx], f"input_{idx}")

        elif "output" in buf.name:
            _list = buf.name.split("_")
            idx = int(_list[1])
            array = _shapeBroadcast(deployer.ctxt, test_outputs[idx], f"output_{idx}")

        elif isinstance(buf, ConstantBuffer):
            array = buf.values
        else:
            raise Exception(f"Unexpected buffer {buf}!")

        typeStr, width = type2TypeStr(buf._type)

        # Word alignment
        mod = (32 // width)
        paddingLength = (mod - (array.size % mod)) % mod
        paddedArray = np.pad(array.flatten(), (0, paddingLength), 'constant')

        paddedArray.astype(typeStr).tofile(path)

    # LMACAN: Dump all global buffers with the "extName" attribute
    os.makedirs(path, exist_ok = True)
    for buf in deployer.ctxt.globalObjects.values():
        if hasattr(buf, "extName"):
            pathName = os.path.join(path, f"{buf.extName}.hex")
            dumpBuffer(buf, pathName)


test_inputs = np.load("../example_network/test_inputs.npz")
test_inputs_header = generateTestInputsHeader(deployer, list(test_inputs.values()), inputTypes, inputOffsets)

test_outputs = np.load("../example_network/test_outputs.npz")
test_outputs_header = generateTestOutputsHeader(deployer, list(test_outputs.values()))

gen_dir = "../gen/test"
os.makedirs(gen_dir, exist_ok=True)
test_inputs_header_file = f"{gen_dir}/test_inputs.h"
test_outputs_header_file = f"{gen_dir}/test_outputs.h"
with open(test_inputs_header_file, "w") as f:
    f.write(test_inputs_header)
with open(test_outputs_header_file, "w") as f:
    f.write(test_outputs_header)
format_c_file(test_inputs_header_file)
format_c_file(test_outputs_header_file)

generateL3HexDump(deployer, "../gen/hex", list(test_inputs.values()), list(test_outputs.values()))
