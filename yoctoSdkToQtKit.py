#! /usr/bin/python3

'''
Created on Mar 17, 2019

@author: Oleg Efremov
'''

import os
import sys
import uuid
import shutil
import argparse
from xml.etree import ElementTree

class CMakeToolSettings:
    def __init__(self, params):
        self.__inputParams = params
        self.__id = "{" + str(uuid.uuid1()) + "}" 

    def getName(self):
        return self.__inputParams.name + " CMake"
        
    def getPath(self):
        path = os.path.join(self.__inputParams.getNativeSysroot(), "usr/bin/cmake")
        
        if (not os.path.isfile(path)):
            raise Exception('Failed to find a CMake tool: ' + path)
        
        return path
    
    def getId(self):
        return self.__id
        
class ToolchainSettings:
    def __init__(self, params):
        self.__inputParams = params
        self.__gccId = "{" + str(uuid.uuid4()) + "}" 
        self.__gppId = "{" + str(uuid.uuid4()) + "}" 
        
    def getGccName(self):
        return self.__inputParams.name + " gcc compiler"

    def getGccPath(self):
        path = self.getTool("gcc")
        return path

    def getGccId(self):
        return self.__gccId

    def getGppName(self):
        return self.__inputParams.name + " g++ compiler"
        
    def getGppPath(self):
        path = self.getTool("g++")
        return path
    
    def getGppId(self):
        return self.__gppId
    
    def getTargetTriple(self):
        return self.__inputParams.getTargetTriple()

    def getTool(self, tool):
        targetSpec = self.__inputParams.getTargetTriple()
        nativeSysroot = self.__inputParams.getNativeSysroot()
        
        path = os.path.join(nativeSysroot, "usr", "bin", targetSpec, targetSpec + "-" + tool)
        
        if (not os.path.isfile(path)):
            raise Exception('Failed to find a compiler: ' + path)
        
        return path

class Params:
    def __init__(self):
        self.isInteractiveMode = True
        self.name = None
        self.sdkPath = None
        self.archPrefix = None
        self.systemName = None
        self.distroName = None
        self.targetSysroot = None
        self.nativeSysroot = None
        self.qtCreatorConfigDir = None
        self.__profileId = "{" + str(uuid.uuid4()) + "}"
        self.__cmakeSettings = CMakeToolSettings(self)
        self.__toolchainSettings = ToolchainSettings(self)

    def getCMakeToolSettings(self):
        return self.__cmakeSettings

    def getToolchainSettings(self):
        return self.__toolchainSettings
    
    def getTargetSysroot(self):
        return os.path.join(self.sdkPath, "sysroots/core2-64-{distro}-linux/".format(distro = self.distroName))

    def getNativeSysroot(self):
        return os.path.join(self.sdkPath, "sysroots/{arch}-{distro}sdk-linux/".format(arch = self.archPrefix, distro = self.distroName))

    def getArchPrefix(self):
        return self.archPrefix

    def getSystemName(self):
        return self.systemName

    def getDistroName(self):
        return self.distroName

    def getProfileId(self):
        return self.__profileId

    def getProfileName(self):
        return self.name + self.__profileId

    def getTargetTriple(self):
        targetTriple = self.getArchPrefix() + "-" + self.getDistroName() + "-" + self.getSystemName()
        return targetTriple
    
    def getQtCreatorConfigDir(self):
        return self.qtCreatorConfigDir
    
    def getCMakeConfiguration(self):
        return
    
    def getFilesystemName(self):
        return

def backupFile(filePath):
    print("Creating a backup copy of " + filePath)
    oldFilePath = os.path.expandvars(filePath)
    i = 1
    isCopyCreated = False
    while (not isCopyCreated):
        newFilePath = oldFilePath + "." + str(i)
        if (not os.path.exists(newFilePath)):
            shutil.copy2(oldFilePath, newFilePath)
            print("Created a backup copy " + newFilePath)
            isCopyCreated = True
            
        i = i + 1
        
def getVariableVal(elements, major, minor):
    dataPath = 'data/[variable="' + str(major)
    
    if not minor == None:
        dataPath = dataPath + "." + str(minor)
        
    dataPath = dataPath + '"]'
    
    data = elements.findall(dataPath)
    if not len(data) == 1:
        print("Unexpected XML structure")
        return None
    
    variable = data[0].findall('variable')
    if not len(variable) == 1:
        print("Unexpected XML structure")
        return None
    
    value = data[0].find('value')
    valueMap = data[0].find('valuemap')
        
    if (value == None and valueMap == None):
        print("Unexpected XML structure")
        return None
        
    if not value == None:
        return value
        
    if not valueMap == None:
        # valueMap.findall('value[@key="Id"]')[0].text
        return valueMap
    
    return None
    
def addCmaketool(path, cmakeToolSettings): 
    print("Adding a new CMake tool to " + path)
    
    allElements = ElementTree.parse(path)
    
    countValueElement = getVariableVal(allElements, 'CMakeTools', 'Count')
    count = int(countValueElement.text) 

    countValueElement.text = str(count + 1)
    
    cmakeToolXml = ('<data>'
                    '<variable>CMakeTools.{index}</variable>'
                    '<valuemap type="QVariantMap">'
                    '<value key="AutoCreateBuildDirectory" type="bool">false</value>'
                    '<value key="AutoDetected" type="bool">false</value>'
                    '<value key="AutoRun" type="bool">true</value>'
                    '<value key="Binary" type="QString">{path}</value>'
                    '<value key="DisplayName" type="QString">{name}</value>'
                    '<value key="Id" type="QString">{id}</value>'
                    '</valuemap>'
                    '</data>').format(path = cmakeToolSettings.getPath(),
                                      name = cmakeToolSettings.getName(),
                                      id = cmakeToolSettings.getId(),
                                      index = count)
    
    cmakeToolElement = ElementTree.fromstring(cmakeToolXml)
    
    allElements.getroot().append(cmakeToolElement)
    allElements.write(path, encoding='utf-8', xml_declaration=True)

def addToolchains(path, toolchainSettings):
    print("Adding a new GCC toolchains to " + path)
    
    allElements = ElementTree.parse(path)
    
    countValueElement = getVariableVal(allElements, 'ToolChain', 'Count')
    count = int(countValueElement.text) 

    countValueElement.text = str(count + 2) # gcc + g++

    toolchainTemplate = (
        '<data>'
        '<variable>ToolChain.{index}</variable>'
        '<valuemap type="QVariantMap">'
        '<value type="QString" key="ProjectExplorer.GccToolChain.OriginalTargetTriple">{targetTriple}</value>'
        '<value type="QString" key="ProjectExplorer.GccToolChain.Path">{path}</value>'
        '<valuelist type="QVariantList" key="ProjectExplorer.GccToolChain.PlatformCodeGenFlags"/>'
        '<valuelist type="QVariantList" key="ProjectExplorer.GccToolChain.PlatformLinkerFlags"/>'
        '<value type="bool" key="ProjectExplorer.ToolChain.Autodetect">false</value>'
        '<value type="QString" key="ProjectExplorer.ToolChain.DisplayName">{name}</value>'
        '<value type="QString" key="ProjectExplorer.ToolChain.Id">ProjectExplorer.ToolChain.Gcc:{id}</value>'
        '<value type="int" key="ProjectExplorer.ToolChain.Language">{langId}</value>'
        '<value type="QString" key="ProjectExplorer.ToolChain.LanguageV2">{langName}</value>'
        '</valuemap>'
        '</data>') 

    gccToolchainXml = toolchainTemplate.format(index = count,
                                               targetTriple = toolchainSettings.getTargetTriple(),
                                               path = toolchainSettings.getGccPath(),
                                               name = toolchainSettings.getGccName(),
                                               id = toolchainSettings.getGccId(),
                                               langId = 1,
                                               langName = 'C')

    gccToolchainElement = ElementTree.fromstring(gccToolchainXml)
    allElements.getroot().append(gccToolchainElement)
     
    gppToolchainXml = toolchainTemplate.format(index = count + 1,
                                               targetTriple = toolchainSettings.getTargetTriple(),
                                               path = toolchainSettings.getGppPath(),
                                               name = toolchainSettings.getGppName(),
                                               id = toolchainSettings.getGppId(),
                                               langId = 2,
                                               langName = 'Cxx')

    gppToolchainElement = ElementTree.fromstring(gppToolchainXml)
    allElements.getroot().append(gppToolchainElement)
    
    allElements.write(path, encoding='utf-8', xml_declaration=True)    
        
def addProfile(path, params, cmakeToolSettings, toolchainSettings): 
    print("Adding a new Kit to " + path)
    
    allElements = ElementTree.parse(path)
    
    countValueElement = getVariableVal(allElements, 'Profile', 'Count')
    count = int(countValueElement.text) 

    countValueElement.text = str(count + 1)

    profileXml = """
         <data>
          <variable>Profile.{index}</variable>
          <valuemap type="QVariantMap">
           <value type="bool" key="PE.Profile.AutoDetected">false</value>
           <value type="QString" key="PE.Profile.AutoDetectionSource"></value>
           <valuemap type="QVariantMap" key="PE.Profile.Data">
            <value type="QString" key="Android.GdbServer.Information"></value>
            <valuelist type="QVariantList" key="CMake.ConfigurationKitInformation">
             <value type="QString">CMAKE_CXX_COMPILER:INTERNAL={gppPath}</value>
             <value type="QString">CMAKE_C_COMPILER:INTERNAL={gccPath}</value>
             <value type="QString">CMAKE_SYSROOT:INTERNAL={targetSysroot}</value>
             <value type="QString">CMAKE_TOOLCHAIN_FILE:INTERNAL={nativeSysroot}/usr/share/cmake/OEToolchainConfig.cmake</value>
            </valuelist>
            <valuemap type="QVariantMap" key="CMake.GeneratorKitInformation">
             <value type="QString" key="ExtraGenerator">CodeBlocks</value>
             <value type="QString" key="Generator">Unix Makefiles</value>
             <value type="QString" key="Platform"></value>
             <value type="QString" key="Toolset"></value>
            </valuemap>
            <value type="QString" key="CMakeProjectManager.CMakeKitInformation">{cmaketoolId}</value>
            <value type="QString" key="Debugger.Information">{{ee8407cc-6668-456e-b67e-435f3beb1413}}</value>
            <value type="QString" key="PE.Profile.Device">Desktop Device</value>
            <value type="QString" key="PE.Profile.DeviceType">Desktop</value>
            <valuelist type="QVariantList" key="PE.Profile.Environment">
             <value type="QString">OECORE_NATIVE_SYSROOT={nativeSysroot}</value>
             <value type="QString">OECORE_TARGET_SYSROOT={targetSysroot}</value>
             <value type="QString">PATH={nativeSysroot}/usr/bin:{nativeSysroot}/bin:{nativeSysroot}/usr/bin/x86_64-{distro}-linux:/usr/bin:/bin</value>
             <value type="QString">SDKTARGETSYSROOT={targetSysroot}</value>
             <value type="QString">PKG_CONFIG_PATH={targetSysroot}/usr/lib/pkgconfig/</value>
            </valuelist>
            <value type="QString" key="PE.Profile.SysRoot">{targetSysroot}</value>
            <value type="QByteArray" key="PE.Profile.ToolChain">{gppId}</value>
            <valuemap type="QVariantMap" key="PE.Profile.ToolChains">
             <value type="QByteArray" key="C">{gccId}</value>
             <value type="QString" key="Cxx">{gppId}</value>
            </valuemap>
            <valuemap type="QVariantMap" key="PE.Profile.ToolChainsV3">
             <value type="QByteArray" key="C">{gccId}</value>
             <value type="QByteArray" key="Cxx">{gppId}</value>
            </valuemap>
            <value type="QString" key="Qbs.KitInformation"></value>
            <value type="QString" key="QtPM4.mkSpecInformation"></value>
            <value type="int" key="QtSupport.QtInformation">-1</value>
           </valuemap>
           <value type="QString" key="PE.Profile.FileSystemFriendlyName">Qemu-x86-64</value>
           <value type="QString" key="PE.Profile.Icon">:///DESKTOP///</value>
           <value type="QString" key="PE.Profile.Id">{profileId}</value>
           <valuelist type="QVariantList" key="PE.Profile.MutableInfo">
            <value type="QString">PE.Profile.SysRoot</value>
           </valuelist>
           <value type="QString" key="PE.Profile.Name">{profileName}</value>
           <value type="bool" key="PE.Profile.SDK">false</value>
           <valuelist type="QVariantList" key="PE.Profile.StickyInfo"/>
          </valuemap>
         </data>""".format(index = count,
                           gppPath = toolchainSettings.getGppPath(),
                           gccPath = toolchainSettings.getGccPath(),
                           gccId = toolchainSettings.getGccId(),
                           gppId = toolchainSettings.getGppId(),
                           cmaketoolId = cmakeToolSettings.getId(),
                           targetSysroot = params.getTargetSysroot(),
                           nativeSysroot = params.getNativeSysroot(),
                           distro = params.getDistroName(),
                           profileId = params.getProfileId(),
                           profileName = params.getProfileName())
  
    profileElement = ElementTree.fromstring(profileXml)
    allElements.getroot().append(profileElement)
     
    allElements.write(path, encoding='utf-8', xml_declaration=True) 

def addKit(params):
    
    cmaketoolsPath = os.path.join(params.getQtCreatorConfigDir(), "cmaketools.xml")
    backupFile(cmaketoolsPath)

    toolchainsPath = os.path.join(params.getQtCreatorConfigDir(), "toolchains.xml") 
    backupFile(toolchainsPath)

    profilesPath = os.path.join(params.getQtCreatorConfigDir(), "profiles.xml") 
    backupFile(profilesPath)

    cmakeToolSettings = params.getCMakeToolSettings();
    addCmaketool(cmaketoolsPath, cmakeToolSettings)

    toolchainSettings = params.getToolchainSettings()
    addToolchains(toolchainsPath, toolchainSettings)

    addProfile(profilesPath, params, cmakeToolSettings, toolchainSettings)
    
def parseArgv(argv, defaultParams):
    argParser = argparse.ArgumentParser(description=
                                        ('Configures a new Qt Creator Kit for the specified Yocto SDK. '
                                         'This utility was tested on Kubuntu 18.04 + Qt Creator 4.8.2 + Yocto release Rocko'),
                                        epilog=
                                        ('Note: it is not recommended to create multiple Qt Kits for one Yocto SDK '
                                         'because Qt Creator does not allow to have multiple compilers with same binary'))
    
    argParser.add_argument('-n', '--name', required=False, default=defaultParams.name, 
                           help='set the new Yocto Qt Kit name')
    
    argParser.add_argument('-d', '--sdkPath', required=False, default=defaultParams.sdkPath, 
                           help='set the directory where the Yocto SDK is installed')
    
    argParser.add_argument('-i', '--interactive', required=False, action='store_true', default=defaultParams.isInteractiveMode, 
                           help='run in interactive mode (not implemented)')
    
    argParser.add_argument('-o', '--distro', required=False, default=defaultParams.getDistroName(), 
                           help='set the distro name')
    
    args = argParser.parse_args()

    if args.name:
        defaultParams.name = args.name 
    
    if args.sdkPath:
        defaultParams.sdkPath = args.sdkPath
        
    if args.distro:
        defaultParams.distroName = args.distro
        
    defaultParams.isInteractiveMode = args.interactive
        
    return defaultParams

def queryParams(defaultParams):
    print("Interactive mode is not implemented, the default setting will be used instead")

    return defaultParams

def getDefaultParams():

    defaultParams = Params()
    defaultParams.name = "Yocto Poky SDK"
    defaultParams.isInteractiveMode = False
    defaultParams.sdkPath = "/opt/poky/2.4.4/"
    defaultParams.archPrefix = "x86_64"
    defaultParams.systemName = "linux"
    defaultParams.distroName = "poky"
    defaultParams.qtCreatorConfigDir = os.path.expandvars("$HOME/.config/QtProject/qtcreator/")
    
    return defaultParams

def main():
    
    defaultParams = getDefaultParams()
    
    params = parseArgv(sys.argv, defaultParams)
    if (params.isInteractiveMode):
        params = queryParams(params)

    addKit(params)
        
### Execution starts here ###
if __name__ == '__main__':
    sys.exit(main())
