get_filename_component(RID_CORE_ROOT "${CMAKE_CURRENT_LIST_DIR}/../../../core" ABSOLUTE)
idf_component_register(SRCS "${RID_CORE_ROOT}/src/rid_core.cpp" INCLUDE_DIRS "${RID_CORE_ROOT}/include")
target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_17)
