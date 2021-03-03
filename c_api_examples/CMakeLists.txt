
cmake_minimum_required(VERSION 3.0)
set(MOCO_INSTALL_DIR "../../../.." CACHE FILEPATH "Path to MoCo root install")

link_directories(${MOCO_INSTALL_DIR}/lib/moco ${MOCO_INSTALL_DIR}/lib/moco/static)

add_executable(c_api_example
        c_api_example.c
)

target_include_directories(c_api_example PRIVATE ${MOCO_INSTALL_DIR}/include)

set_target_properties(c_api_example PROPERTIES LINKER_LANGUAGE CXX
                                               C_STANDARD 99)

target_link_libraries(c_api_example PUBLIC
    zmq_mpd
    
    pthread
)
