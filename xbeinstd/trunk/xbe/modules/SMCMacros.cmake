# -*- mode: cmake; -*-
#
# This file contains a convenience macro for the use with the SMC state machine compiler
#

function(add_state_machine FSM_NAME)
  if(SMC_FOUND)
    if ("${CMAKE_CURRENT_SOURCE_DIR}/${FSM_NAME}.sm" IS_NEWER_THAN "${CMAKE_CURRENT_SOURCE_DIR}/${FSM_NAME}_sm.cpp")
        add_custom_command(OUTPUT ${CMAKE_CURRENT_SOURCE_DIR}/${FSM_NAME}_sm.cpp ${CMAKE_CURRENT_SOURCE_DIR}/${FSM_NAME}_sm.h
          COMMAND ${JAVA_RUNTIME} -jar ${SMC_JAR} -c++ ${CMAKE_CURRENT_SOURCE_DIR}/${FSM_NAME}.sm
          COMMAND ${CMAKE_COMMAND} -E touch_nocreate ${CMAKE_CURRENT_SOURCE_DIR}/${FSM_NAME}_sm.cpp
          COMMAND ${CMAKE_COMMAND} -E touch_nocreate ${CMAKE_CURRENT_SOURCE_DIR}/${FSM_NAME}_sm.h
          WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
          MAIN_DEPENDENCY ${CMAKE_CURRENT_SOURCE_DIR}/${FSM_NAME}.sm
          COMMENT "Compiling '${FSM_NAME}' state machine...")
    endif ("${CMAKE_CURRENT_SOURCE_DIR}/${FSM_NAME}.sm" IS_NEWER_THAN "${CMAKE_CURRENT_SOURCE_DIR}/${FSM_NAME}_sm.cpp")
  else(SMC_FOUND)
    if ("${CMAKE_CURRENT_SOURCE_DIR}/${FSM_NAME}.sm" IS_NEWER_THAN "${CMAKE_CURRENT_SOURCE_DIR}/${FSM_NAME}_sm.cpp")
      message(FATAL_ERROR "The '${FSM_NAME}' StateMachine needs to be updated but the StateMachineCompiler (SMC) could not be found!")
    endif ("${CMAKE_CURRENT_SOURCE_DIR}/${FSM_NAME}.sm" IS_NEWER_THAN "${CMAKE_CURRENT_SOURCE_DIR}/${FSM_NAME}_sm.cpp")
  endif(SMC_FOUND)
endfunction(add_state_machine)
