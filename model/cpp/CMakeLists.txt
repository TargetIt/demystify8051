cmake_minimum_required(VERSION 3.14)
project(echo_8051_iss LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(echo_8051_iss STATIC
    src/echo_8051.cpp
)
target_include_directories(echo_8051_iss PUBLIC include)

add_executable(test_iss test/test_main.cpp)
target_link_libraries(test_iss echo_8051_iss)

if(MSVC)
    target_compile_options(echo_8051_iss PRIVATE /W3 /EHsc)
else()
    target_compile_options(echo_8051_iss PRIVATE -Wall -O2 -g)
endif()
