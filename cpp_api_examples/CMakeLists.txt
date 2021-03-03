Project(Moco_SDK_Examples)
cmake_minimum_required(VERSION 3.4)
if(WIN32)
    set(moco_path_default "c:/Program\ Files/Motive/lib/moco/cmake")
elseif(LINUX)
    set(moco_path_default "/usr/lib/moco/cmake")
elseif(APPLE)
    set(moco_path_default "/Applications/Motive/lib/moco/cmake")
endif()

find_package(Moco CONFIG REQUIRED PATHS ${moco_path_default})
find_package(Threads REQUIRED)
MACRO(SDKExample name)
add_executable(${name} ${name})

set_target_properties(${name} PROPERTIES
                    LINKER_LANGUAGE CXX
                    CXX_STANDARD 14
                    CMAKE_POSITION_INDEPENDENT_CODE ON
)

target_link_libraries(${name} PUBLIC motive::moco_api)
ENDMACRO()

SDKExample(buffer_example)
SDKExample(manager_example)
SDKExample(simple_send_receive_packet)
SDKExample(position_example)
SDKExample(spring_example)
SDKExample(multi-dof_example)
