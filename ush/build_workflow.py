import subprocess
import os
import argparse
import detect_machine as dm

def parse_arguments():
    # Get some system info to use in setting up defaults for argparse
    
    workflow_dir: str = os.path.dirname(os.getcwd())
    sorc_dir: str = f"{workflow_dir}/sorc"

    parser = argparse.ArgumentParser(description="Build the AQM Workflow")
    
    parser.add_argument("--build-all", action="store_true")
    parser.add_argument("--build-ufswm", action="store_true")
    parser.add_argument("--build-ufs-utils", action="store_true")
    parser.add_argument("--build-aqm-utils", action="store_true")
    parser.add_argument("--build-nexus", action="store_true")
    parser.add_argument("--build-upp", action="store_true")
    parser.add_argument("-c", "--compiler", nargs=1, type=str, default="Intel")
    parser.add_argument("--ccpp-suites", nargs="?", type=str, default="FV3_GFS_v16")
    #parser.add_argument(--enable-options=?*) ENABLE_OPTIONS=${1#*=} ;;
    #parser.add_argument(--disable-options=?*) DISABLE_OPTIONS=${1#*=} ;;
    parser.add_argument("--remove", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--build", action="store_true")
    #parser.add_argument("--move", action="store_true")
    parser.add_argument("--build-dir", nargs=1, type=str, default=f'{workflow_dir}/build')
    parser.add_argument("--install-dir", nargs=1, type=str, default=f'{workflow_dir}/build')
    #parser.add_argument("--bin-dir")
    parser.add_argument("--sorc-dir", default=f"{workflow_dir}/sorc", help=argparse.SUPPRESS)
    parser.add_argument("--build-type", nargs=1, type=str, default="Release")
    parser.add_argument("--build-jobs", nargs=1, type=int, default=4)
    parser.add_argument("-v", "--verbose", action="store_true")
    #parser.add_argument("--use-sub-modules")

    return parser.parse_args()

class ArgValidaton:
    
    def __init__(self, args):
        self.subcomponent(args)
        self.directories(args)
        self.options(args)
        self.machine_id: str = dm.get_machine_id()

    def options(self, args):
        self.remove: bool = args.remove
        self.resume: bool = args.resume
        self.clean: bool = args.clean
        self.build: bool = args.build
        self.build_type: str = args.build_type
        self.build_jobs: int = args.build_jobs
        self.verbose: bool = args.verbose
        self.ccpp_suites: str = args.ccpp_suites

    def directories(self, args):
        self.build_dir: str = args.build_dir
        self.install_dir: str = args.install_dir
        self.sorc_dir: str = args.sorc_dir

    def subcomponent(self, args):
        self.build_all: bool = args.build_all
        self.build_ufswm: bool = args.build_ufswm
        self.build_ufs_utils: bool = args.build_ufs_utils
        self.build_aqm_utils: bool = args.build_aqm_utils
        self.build_nexus: bool = args.build_nexus
        self.build_upp: bool = args.build_upp

        if self.build_all:
            self.build_ufswm = True
            self.build_ufs_utils = True
            self.build_aqm_utils = True
            self.build_nexus = True
            self.build_upp = True

def do_build_ufswm(validated_args):
    print("Building UFSWM")

    if not os.path.isdir(f"{validated_args.build_dir}/ufs-weather-model"):
        os.mkdir(f"{validated_args.build_dir}/ufs-weather-model") 
    else:
        print("ufs-weather-model build dir exists.. Not creating")

    env_cmake_c_compiler = os.environ['CMAKE_C_COMPILER']
    env_cmake_cxx_compiler = os.environ['CMAKE_CXX_COMPILER']
    env_cmake_fort_compiler = os.environ['CMAKE_Fortran_COMPILER']
    env_mapl_root = os.environ['mapl_ROOT']

    popen_commands: str = f"""
module use ufs-weather-model/modulefiles
module load ufs_{validated_args.machine_id.lower()}.intel
cmake \
-DCCPP_SUITES={validated_args.ccpp_suites} \
-DCMAKE_C_COMPILER={env_cmake_c_compiler} \
-DCMAKE_CXX_COMPILER={env_cmake_cxx_compiler} \
-DCMAKE_Fortran_COMPILER={env_cmake_fort_compiler} \
-DCMAKE_BUILD_TYPE={validated_args.build_type} \
-DCMAKE_MODULE_PATH={env_mapl_root}/share/MAPL/cmake \
-D32BIT=ON -DINLINE_POST=ON -DAPP=ATMAQ \
-S {validated_args.sorc_dir}/ufs-weather-model \
-B {validated_args.build_dir}/ufs-weather-model
"""

    #Grab current environment
    current_env = os.environ.copy()
    process = subprocess.Popen(popen_commands, shell=True,
                     executable="/bin/bash", stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, env=current_env)
    stdout, stderr = process.communicate()
    process.wait()
    process2 = subprocess.Popen(["make", "-j", "8", "-C", f"{validated_args.build_dir}/ufs-weather-model"])
    stdout2, stderr2 = process2.communicate()
    process2.wait()
    pass

def do_build_ufs_utils(validated_args):
    print("Building UFS_UTILS")

    # Build UFS utilities
    if not os.path.isdir(f"{validated_args.build_dir}/UFS_UTILS"):
        os.mkdir(f"{validated_args.build_dir}/UFS_UTILS") 
    else:
        print("Build Dir Exists.. Not creating")

    popen_commands: str = f"""
module use {validated_args.sorc_dir}/UFS_UTILS/modulefiles
module load build.{validated_args.machine_id.lower()}.intel
cmake --verbose\
-DCMAKE_BUILD_TYPE={validated_args.build_type} -DBUILD_TESTING=OFF -DFRENCTOOLS=OFF \
-DICEBLEND=OFF -DSNOW2MDL=OFF -DGCYCLE=OFF -DGRIDTOOLS=OFF -DOROG_MASK_TOOLS=OFF \
-DSFC_CLIMO_GEN=OFF -DVCOORD_GEN=OFF -DFVCOMTOOLS=OFF -DGBLEVENTS=OFF \
-DOCEAN_MERGE=OFF -DCPLD_GRIDGEN=OFF -DWEIGHT_GEN=OFF \
-S {validated_args.sorc_dir}/UFS_UTILS -B {validated_args.build_dir}/UFS_UTILS
"""
    
    #Grab current environment
    current_env = os.environ.copy()
    process = subprocess.Popen(popen_commands, shell=True,
                     executable="/bin/bash", stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, env=current_env)
    stdout, stderr = process.communicate()
    process.wait()
    process2 = subprocess.Popen(["make", "-j", "8", "-C", f"{validated_args.build_dir}/UFS_UTILS"])
    stdout2, stderr2 = process2.communicate()
    process2.wait()
    pass

def do_build_aqm_utils(validated_args):
    print("Building AQM-UTILS")

    popen_commands: str = f"""
module use {validated_args.sorc_dir}/AQM-utils/modulefiles
module load build_{validated_args.machine_id.lower()}.intel
cmake --verbose \
-DCMAKE_BUILD_TYPE={validated_args.build_type} \
-S {validated_args.sorc_dir}/AQM-utils -B {validated_args.build_dir}/AQM-utils
"""
    current_env = os.environ.copy()
    process = subprocess.Popen(popen_commands, shell=True,
                     executable="/bin/bash", stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, env=current_env)
    stdout, stderr = process.communicate()
    process.wait()
    process2 = subprocess.Popen(["make", "-j", "8", "-C", f"{validated_args.build_dir}/AQM-utils"])
    stdout2, stderr2 = process2.communicate()
    process2.wait()

    pass

# def do_build_nexus(validated_args):
#     print("Building NEXUS")

#     popen_commands: str = f"""
# module use {validated_args.sorc_dir}/arl_nexus/modulefiles
# module load ufs_{validated_args.machine_id.lower()}.intel
# cmake \
# -DCMAKE_BUILD_TYPE={validated_args.build_type} \
# -S {validated_args.sorc_dir}/arl_nexus -B {validated_args.build_dir}/arl_nexus
# """
#     current_env = os.environ.copy()
#     process = subprocess.Popen(popen_commands, shell=True,
#                      executable="/bin/bash", stdout=subprocess.PIPE,
#                      stderr=subprocess.PIPE, env=current_env)
#     stdout, stderr = process.communicate()
#     process.wait()
#     process2 = subprocess.Popen(["make", "-j", "8", "-C", f"{validated_args.build_dir}/arl_nexus"])
#     stdout2, stderr2 = process2.communicate()
#     process2.wait()
    
#     pass

def setup_aqm_utils(validated_args, build_in):
    print("Setting up AQM-utils")

    aqm_utils_lua_prefix: str = "build_"
    aqm_utils_lua_suffix: str = ".intel"
    aqm_utils_dirname: str = "AQM-utils"
    aqm_utils_cmake: str = f"-DCMAKE_BUILD_TYPE={validated_args.build_type}"
    aqm_utils_enabled: bool = True if validated_args.build_upp else False

    build_in.add_component(aqm_utils_dirname, aqm_utils_lua_prefix, aqm_utils_lua_suffix, aqm_utils_cmake, aqm_utils_enabled)

def setup_nexus(validated_args, build_in):
    print("Setting up NEXUS")

    nexus_lua_prefix: str = "ufs_"
    nexus_lua_suffix: str = ".intel"
    nexus_dirname: str = "arl_nexus"
    nexus_cmake: str = f"-DCMAKE_BUILD_TYPE={validated_args.build_type}"
    nexus_enabled: bool = True if validated_args.build_upp else False

    build_in.add_component(nexus_dirname, nexus_lua_prefix, nexus_lua_suffix, nexus_cmake, nexus_enabled)

def setup_upp(validated_args, build_in):
    print("Setting up UPP")

    upp_lua_prefix: str = ""
    upp_lua_suffix: str = ""
    upp_dirname: str = "UPP"
    upp_cmake: str = f"""-DCMAKE_BUILD_TYPE={validated_args.build_type} \
-DBUILD_WITH_IFI=OFF -DBUILD_WITH_GTG=OFF -DBUILD_WITH_WRFIO=ON"""
    upp_enabled: bool = True if validated_args.build_upp else False

    build_in.add_component(upp_dirname, upp_lua_prefix, upp_lua_suffix, upp_cmake, upp_enabled)

class Build:
    
    class Component:
        def __init__(self, dirname, lua_prefix, lua_suffix, cmake, enabled):
            self.dirname: str = dirname
            self.lua_prefix: str = lua_prefix
            self.lua_suffix: str = lua_suffix
            self.cmake:str = cmake
            self.enabled: bool = enabled
    
    class Process:
        def __init__(self, comp_name, process, stdout, stderr):
            self.comp_name: str = comp_name
            self.process = process
            self.stdout = stdout
            self.stderr = stderr

    def __init__(self):
        self.name = __name__
        self.component_list: list[Component] = []
        self.process_list: list[Process] = []
    
    def add_component(self, dirname, lua_prefix, lua_suffix, cmake, enabled):
        newComponent = self.Component(dirname, lua_prefix, lua_suffix, cmake, enabled)
        self.component_list.append(newComponent)
        print(f"Added Component {dirname}")
    
    def add_process(self, comp_name, process, stdout, stderr):
        newProcess = self.Process(comp_name, process, stdout, stderr)
        self.process_list.append(newProcess)
        print(f"Added Process {comp_name}")
    
    def run(self, validated_args):
        
        for component in self.component_list:
            if component.enabled:
                current_env = os.environ.copy()
                job_command = f"""
module use {validated_args.sorc_dir}/{component.dirname}/modulefiles
module load {component.lua_prefix}{validated_args.machine_id.lower()}{component.lua_suffix}
cmake {component.cmake} -S {validated_args.sorc_dir}/{component.dirname} -B {validated_args.build_dir}/{component.dirname}
make -j 8 -C {validated_args.build_dir}/{component.dirname}
"""
                print(job_command)
                process = subprocess.Popen(job_command, shell=True,
                                            executable="/bin/bash", stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE, env=current_env)
                stdout, stderr = process.communicate()
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                self.add_process(component.dirname, process, stdout, stderr)
                process.wait()
            else:
                print(f"Component {component.dirname} Not Enabled.")
        
        for process in self.process_list:
            process.wait()
        

def main():
    args = parse_arguments()
    validated_args = ArgValidaton(args)
    thisBuild = Build()
    
    os.mkdir(validated_args.build_dir) if not os.path.isdir(validated_args.build_dir) else print("Build Dir Exists.. Not creating")

    # do_build_ufswm(validated_args) if validated_args.build_ufswm else print("Skipping UFSWM Build")
    # do_build_ufs_utils(validated_args) if validated_args.build_ufs_utils else print("Skipping UFS_UTILS Build")
    # do_build_aqm_utils(validated_args) if validated_args.build_aqm_utils else print("Skipping AQM_UTILS Build")
    setup_aqm_utils(validated_args, thisBuild)
    setup_nexus(validated_args, thisBuild)
    setup_upp(validated_args, thisBuild)
    thisBuild.run(validated_args)
    print("Made it to the end")

if __name__ == "__main__":
    main()