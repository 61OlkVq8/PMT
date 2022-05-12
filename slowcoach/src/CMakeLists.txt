cmake_minimum_required(VERSION 3.4.3)

project("SlowCoach")

find_package(LLVM REQUIRED CONFIG "10.0.0")
find_package(Clang REQUIRED "10.0.0")

find_package(Boost COMPONENTS log log_setup REQUIRED)

include_directories("${LLVM_INCLUDE_DIRS}"
    "${CMAKE_CURRENT_SOURCE_DIR}")
link_directories("${LLVM_LIBRARY_DIRS}")

set(REQUIRED_LLVM_LIBRARIES
    )
set(REQUIRED_CLANG_LIBRARIES
    clangASTMatchers
    clangTooling
    clangBasic
    )

set(CMAKE_C_COMPILER clang)
set(CMAKE_CXX_COMPILER clang++)

set(CMAKE_CXX_STANDARD 14)

set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -Wall -std=c++14 -ggdb -O2")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -Wall -std=c++14 -O2")

add_definitions(-DCMAKE_SOURCE_DIR="${CMAKE_SOURCE_DIR}" "-DBOOST_LOG_DYN_LINK")

add_executable(slowcoach main.cpp OperatorManager.cpp Mutant.cpp MutantManager.cpp
    Operator.cpp
    config.cpp

    operators/FastpathCondOperator.cpp
    operators/FastpathOperator.cpp
    operators/DummyOperator.cpp
    operators/RedunSyncOperator.cpp
    operators/RedunOpOperator.cpp
    operators/RedunOpDeclOperator.cpp
    operators/OblivionOperator.cpp
    operators/SlowpathOperator.cpp
    operators/FuncOperator.cpp
    operators/LazyUpdateOperator.cpp
    operators/LocalVarOperator.cpp
    operators/DeclOperator.cpp
    operators/RedunOperation.cpp
    operators/RedunOpLoopOperator.cpp
    operators/LoopUnbreakOperator.cpp
    )

target_link_libraries(slowcoach
    ${REQUIRED_CLANG_LIBRARIES}
    ${REQUIRED_LLVM_LIBRARIES}
    Boost::log
    Boost::log_setup
    )
