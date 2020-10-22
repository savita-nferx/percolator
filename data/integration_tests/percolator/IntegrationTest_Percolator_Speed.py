# Marcus Andersson - Percolator Project
# Script that tests the performances of percolator

# Add the flag -h with this script to see details about arguments.
# psutil is imported in the case that the script should wait for other integration-test scripts to finish.
# This script relies on the output generated by the C++ source code.

pathToOutputData = "@pathToOutputData@"
pathToTestScripts = "@pathToTestScripts@"
pathToBinaries = "@pathToBinaries@"

import os
import sys
import re

from argparse import ArgumentParser
import time
import contextlib
import subprocess
from subprocess import Popen, PIPE
from decimal import Decimal
import pathlib
import datetime
from pathlib import Path
import urllib
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import tarfile

temporaryFile = "tempPOut.xml"
lineSeparatingText = "-----------------------------------"

testDataFileName = "Pandey.25M.tab"
testDataFullPath = pathToOutputData + "/" + testDataFileName
downloadedDataFileName = "Pandey.25M.tar.gz"
url = "https://kth.box.com/shared/static/t3dgd186n3ckfj5qvhpxga4haiz8lmh8.gz"
processText = 'IntegrationTest_Percolator_Speed.py'

def checkIfTestDataExist():
    return Path(testDataFullPath).is_file()

def downloadTestData():
    req = Request(url)
    site = urlopen(req, timeout=20)
    meta = site.info()
    file_size = int(meta.get_all("Content-Length")[0])
    print ("Downloading: %s Bytes: %s" % (downloadedDataFileName, file_size))
    f = open(pathToOutputData + "/" + downloadedDataFileName, 'wb')
    file_size_dl = 0
    block_sz = 8192
    prevDownloadProgress = 0
    while True:
        buffer = site.read(block_sz)
        if not buffer:
            break
        file_size_dl += len(buffer)
        f.write(buffer)
        downloadProgress = file_size_dl * 100. / file_size
        status = r"%10d  [%.0f%%]" % (file_size_dl, downloadProgress)
        status = status + chr(8)*(len(status)+1)
        if (downloadProgress - prevDownloadProgress > 1. or downloadProgress > 99.9):
            print (status, end="")
            sys.stdout.flush()
            prevDownloadProgress = downloadProgress
    f.close()
    print("\nDownload complete.\n")

def extractTarFile(fname):
    tar = tarfile.open(fname, "r")
    tar.extractall(testDataFolderPath)
    tar.close()

def getArguments():
    parser = ArgumentParser(description="Measure speed of the Percolator application.")
    parser._action_groups.pop()
    #required = parser.add_argument_group('Required arguments')
    optional = parser.add_argument_group('Optional arguments')

    optional.add_argument('-d','--data', type=str, default = "" , metavar='', required=False, help="Path to input-data used by percolator.")
    optional.add_argument('-r','--runs', type=int, metavar='', default=3, required=False, help="Number of tests to evaluate.")
    optional.add_argument('-f','--flags', type=str, default = "" , metavar='', required=False, help="Flags to use with the executable.")
    optional.add_argument('-a','--await_tests', default=False, action="store_true", required=False, help="Wait for others processes running this script to finish before starting.")
    optional.add_argument('-p','--processes', nargs='+', type=int, metavar='',required=False, help="Other test-PIDs to wait for before starting test(s).")
    optional.add_argument('-c','--comments', type=str, default="", metavar='', required=False, help="Comments regarding test details.")
    return parser.parse_args()

def awaitOtherTasks(args):
    if(args.processes is not None):
        waitForProcesses(args.processes)
    if(args.await_tests is True):
        waitForOtherTests()

#waitForProcess(pid) could cause the computer to wait indefinitely if stuck in a race condition. It is assumed that this will not occur normally however.
#Example of eternal wait scenario: A user spawns 2 processes, let's call them A and B. B waits for A to finish, but when A is finished another process spawns with the same pid as A had. B may fail to notice this.
def waitForProcess(pid):
    numIterations = 0
    delayMultiplier = 1
    while(True):
        if psutil.pid_exists(pid):
            if numIterations == 0 or numIterations > 60*delayMultiplier:
                delayMultiplier = delayMultiplier * 2
                numIterations = 1
                print("Waiting for PID " + str(pid) + " to finish. (" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ")")
            time.sleep(45)
        else:
            return
        numIterations += 1

def waitForProcesses(pids):
    if pids is None:
        return
    for p in pids:
        waitForProcess(p)

def waitForOtherTests():
    thisPid = os.getpid()
    parentPid = psutil.Process(thisPid).ppid()
    allProcesses = []
    for p in psutil.process_iter():
        if thisPid == p.pid or parentPid == p.pid:
            continue
        if processText in p.name() or processText in ' '.join(p.cmdline()):
            allProcesses.append(p.pid)
    waitForProcesses(allProcesses)

def removeTemporaryFile():
    with contextlib.suppress(FileNotFoundError):
        os.remove(temporaryFile)

def getTerminalCommand(flags, data):
    result = pathToBinaries + "/percolator "
    result += "-X " + temporaryFile
    result += " " + data
    result += " " + flags
    result = result.split(' ')
    result = list(filter(None, result))
    return result

def getRunTime(resultStr):
    lines = resultStr.splitlines()
    last_line = lines[-1]
    runTime = re.findall(r"[+]?\d*\.\d+|\d+", last_line)
    runTime = [float(i) for i in runTime]
    return runTime

def printInfoBeforeStart(args):
    print("PID:\t\t\t" + str(os.getpid()))
    print("Flags:\t\t\t" + str(args.flags))
    print("Input:\t\t\t" + str(args.data))
    print("Await PIDs:\t\t" + str(args.processes))
    print("Await other tests?\t" + str(args.await_tests))
    print("Number of iterations:\t" + str(args.runs))
    print("Comments:\t\t" + str(args.comments))
    print("Testing command:\t" + str(getTerminalCommand(args.flags, args.data)) )

def getRunTimes(args):
    runTimes = []
    for i in range(1,args.runs+1):
        terminalCommand = getTerminalCommand(args.flags,args.data)
        p = subprocess.Popen(terminalCommand, stderr=PIPE , stdout=subprocess.DEVNULL , text=True)
        print("Running subprocess: " + str(p.pid))
        p.wait()
        removeTemporaryFile()
        runTime = getRunTime(p.stderr.read())
        runTimes.append(runTime)
    return runTimes

def printResults(runTimes):
    print(lineSeparatingText)
    numElements = len(runTimes)
    totalCPUSec = 0
    totalWallSec = 0
    minCPUSec = 99999999999
    minWallSec = 99999999999
    maxCPUSec = -99999999999
    maxWallSec = -99999999999
    print("Execution time in CPU and wall clock seconds, precision set to 3 decimals.")

    for i in range(0,numElements):
        cpuSec = runTimes[i][0]
        wallSec = runTimes[i][1]
        totalCPUSec += cpuSec
        totalWallSec += wallSec
        minCPUSec = min(minCPUSec, cpuSec)
        minWallSec = min(minWallSec, wallSec)
        maxCPUSec = max(maxCPUSec, cpuSec)
        maxWallSec = max(maxWallSec, wallSec)
        print("Run {}\tCPU: {:.3f} Wall: {}".format(i+1, cpuSec, int(wallSec)))
    print(lineSeparatingText)
    print("Max\tCPU: {:.3f} Wall: {}".format(maxCPUSec, int(maxWallSec)) ) 
    print("Min\tCPU: {:.3f} Wall: {}".format(minCPUSec, int(minWallSec)) )
    print("Mean\tCPU: {:.3f} Wall: {}".format(totalCPUSec/numElements, Decimal('{0:.3f}'.format(totalWallSec/numElements)).normalize() ) ) 

def getDataFromUrl(args):
    if len(args.data) == 0 and checkIfTestDataExist() is False:
        try:
            downloadTestData()
        except HTTPError as e:
            print("Failed to download test-data. HTTP Error code: ", e.code)
            return False
        except URLError as e:
            print("Failed to download test-data. Reason: ", e.reason)
            return False
        except:
            print("Failed to download test-data.")
            return False
            
        print("Extracting...")
        extractTarFile(testDataFolderPath + "/" + downloadedDataFileName)
        print("Done extracting.")
    if(len(args.data) == 0):
        args.data = testDataFullPath
    return True

args = getArguments()
if args.await_tests is True or args.processes is not None:
    import psutil

awaitOtherTasks(args)
success = getDataFromUrl(args)

if success == True:
    printInfoBeforeStart(args)
    runTimes = getRunTimes(args)
    printResults(runTimes)

if success==True:
    print("...TEST SUCCEEDED")
    exit(0)
else:
    print("...TEST FAILED")
    exit(1)

