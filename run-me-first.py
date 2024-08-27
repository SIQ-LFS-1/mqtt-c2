import os
import sys
import importlib
import subprocess
from datetime import datetime
from os import path as directoryPath
from os.path import exists as checkExistence

############################################################################################
# Banner function...


def infoBanner():
    print("\n[ WEBIDENCE-MQTT ] Developed By Aayush Rajthala!\n")


infoBanner()

############################################################################################
# ENVIRONMENT FUNCTIONS & VARIABLES

STATUSCODE = ["ERROR", "INFO", "SUCCESS"]


def getFullPath(pathValue):
    return directoryPath.normpath(directoryPath.abspath(pathValue))


def getFileSize(file):
    return directoryPath.getsize(file)


def isFileEmpty(pathValue):
    return getFileSize(pathValue) == 0


def isWin():
    # Returns True, For Windows
    # Returns False, For Linux & Mac
    return os.name == "nt"


def clear_screen():
    if isWin():
        os.system("cls")
    else:
        os.system("clear")

    infoBanner()


def printMessage(type, message):
    colorCode = 33

    if type == "ERROR":
        colorCode = 31

    elif type == "SUCCESS":
        colorCode = 32

    else:
        type = "INFO"
        colorCode = 33

    print(f"\n--[\033[1;{colorCode}m {type} \033[0m]--[ {message} ]\n")

    return


############################################################################################
# Function to Check and Install Missing Libraries


def check_and_install_libraries(required_libraries):
    for library in required_libraries:
        try:
            # Attempt to import the library
            importlib.import_module(library)
        except ImportError:
            printMessage(STATUSCODE[0], f"Library '{library}' not found. Installing...")
            if library == "dotenv":
                library = "python-dotenv"
            elif library == "paho.mqtt":
                library = "paho-mqtt==1.6.1"

            subprocess.check_call([sys.executable, "-m", "pip", "install", library])


required_libraries = ["psutil", "dotenv", "paho.mqtt", "pythonping"]

# Run the library check
check_and_install_libraries(required_libraries)

############################################################################################
# Loading Script Paths based on OS...

envFilepath = getFullPath(".env")
envJsonFilepath = getFullPath("credentials/env.json")
topicsFilepath = getFullPath("credentials/topics.json")
vmInfoFilepath = getFullPath("credentials/vmInfo.json")

############################################################################################
# Checking Dependencies...


def checkDependencies():
    try:
        clear_screen()

        MISSING = False
        EMPTY = False

        # Define all required files
        required_files = [envFilepath, envJsonFilepath, topicsFilepath, vmInfoFilepath]

        printMessage(STATUSCODE[1], "Dependencies Check")
        for file in required_files:
            if not checkExistence(file):
                print(f"\033[1;31mMissing \033[0m: {file}")
                MISSING = True

            elif isFileEmpty(file):
                print(f"\033[1;34mEmpty \033[0m: {file}")
                EMPTY = True

            else:
                print(f"\033[1;32mFound \033[0m: {file}")

        print("\n")

        if MISSING or EMPTY:
            exit()

        # If all files exist, return successfully
        return

    except Exception as error:
        printMessage(STATUSCODE[0], error)


if __name__ == "__main__":
    checkDependencies()
