# Function to create the flags for hyperflash
# Saves the result into the `out_var`
function(gvsoc_flags_add_files_to_hyperflash out_var files_var)
	# LMACAN: The double variable expansion is needed because the first
	# expansion gets us the variable name, the second one actual list elements
	set(flags ${${files_var}})
	list(TRANSFORM flags PREPEND "--flash-property=")
	list(TRANSFORM flags APPEND "@hyperflash:readfs:files")
	set(${out_var} ${flags} PARENT_SCOPE)
endfunction()

# The macro creates a new gvsoc_<name> cmake target which executes the final
# binary on the gvsoc simulator. To give extra flags to the gvsoc command, set
# the GVSOC_EXTRA_FLAGS variable.
macro(add_gvsoc_emulation name target)
	if(NOT DEFINED ENV{GVSOC})
		message(FATAL_ERROR "Environment variable GVSOC not set")
	endif()
	set(GVSOC_WORKDIR ${CMAKE_BINARY_DIR}/gvsoc_workdir)
	make_directory(${GVSOC_WORKDIR})
	set(GVSOC_BINARY "${CMAKE_BINARY_DIR}/${name}")
	set(GVSOC_COMMAND $ENV{GVSOC} --target=${target} --binary=${GVSOC_BINARY} --work-dir=${GVSOC_WORKDIR} ${GVSOC_EXTRA_FLAGS} image flash run)
	list(JOIN GVSOC_COMMAND " " GVSOC_COMMAND_STRING)
	add_custom_target(gvsoc_${name}
		DEPENDS ${name}
		COMMAND echo "${GVSOC_COMMAND_STRING}" && ${GVSOC_COMMAND}
		COMMENT "Simulating deeploytest ${name} with gvsoc for the target ${target}"
		POST_BUILD
		USES_TERMINAL
		VERBATIM
	)
endmacro()
