SET(CMAKE_SYSTEM_NAME Windows)

# specify the cross compiler
find_file(MINGWV NAMES i586-mingw32msvc-gcc i586-mingw32msvc-g++ PATHS
			/usr/bin
			/usr/local/bin)
if(NOT MINGWV)
  set(MINGW_PREFIX "/usr/bin/i686-pc-mingw32-")
else(NOT MINGWV)
  set(MINGW_PREFIX "/usr/bin/i586-mingw32msvc-")
endif(NOT MINGWV)

# set(CMAKE_AR ${MINGW_PREFIX}ar)
# set(CMAKE_RANLIB ${MINGW_PREFIX}ranlib)
# set(CMAKE_LINKER ${MINGW_PREFIX}ld)
set(CMAKE_C_COMPILER ${MINGW_PREFIX}gcc)
set(CMAKE_CXX_COMPILER ${MINGW_PREFIX}g++)
set(CMAKE_RC_COMPILER ${MINGW_PREFIX}windres)
set(CMAKE_EXECUTABLE_SUFFIX ".exe")

# Boost Configuration
SET(Boost_COMPILER "-gcc45")
SET(Boost_USE_STATIC_LIBS ON) 
# where is the target environment
SET(CMAKE_FIND_ROOT_PATH /usr/i686-pc-mingw32;/usr/i586-mingw32msvc;/usr/i686-pc-mingw32/sys-root/mingw;/usr/i586-mingw32msvc/sys-root/mingw;
			  /home/USERNAME/i586-mingw32msvc;/home/USERNAME/i686-pc-mingw32;
			  ${PROJECT_SOURCE_DIR}/../libs;${PROJECT_SOURCE_DIR}/libs;${PROJECT_SOURCE_DIR}/../../libs)

# search for programs in the build host directories
SET(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
# for libraries and headers in the target directories
SET(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
SET(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)


