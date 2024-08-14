import os
import json
import uuid
import shlex
import psutil
import socket
import signal
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from os import path as directoryPath
from os.path import exists as checkExistence

############################################################################################
# Banner function...


def infoBanner():
    print("\n[ WEBIDENCE-MQTT ] Developed By Aayush Rajthala!\n")


def successBanner():
    # Test Completed ASCII ART...
    print("\n")
    print(
        "╔╦╗╔═╗╔═╗╔╦╗  ╔═╗╔═╗╔╦╗╔═╗╦  ╔═╗╔╦╗╔═╗╔╦╗\n ║ ║╣ ╚═╗ ║   ║  ║ ║║║║╠═╝║  ║╣  ║ ║╣  ║║\n ╩ ╚═╝╚═╝ ╩   ╚═╝╚═╝╩ ╩╩  ╩═╝╚═╝ ╩ ╚═╝═╩╝"
    )


infoBanner()

############################################################################################
# ENVIRONMENT FUNCTIONS & VARIABLES

STATUSCODE = ["ERROR", "INFO", "SUCCESS"]


def getFullPath(pathValue):
    return directoryPath.normpath(directoryPath.abspath(pathValue))


def getCurrentDateTime():
    currentdatetime = datetime.now().strftime("%b-%d-%Y-%HH-%Mm-%Ss")
    return currentdatetime


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

    print(f"--[\033[1;{colorCode}m {type} \033[0m]--[ {message} ]\n")

    return


def getTester(ip_address):
    for VM in TESTERINFO:
        return VM["tester"] if ip_address in VM["hosts"] else None


############################################################################################
# Assigning filepaths to a variable...

envFilepath = getFullPath(".env")
envjsonFilepath = getFullPath("credentials/env.json")
vmInfoFilepath = getFullPath("credentials/vmInfo.json")
topicsFilepath = getFullPath("credentials/topics.json")

############################################################################################
# Checking Dependencies...


def checkDependencies():
    clear_screen()

    # Define all required files
    required_files = [envFilepath, vmInfoFilepath, topicsFilepath]

    # Check for the existence of each required file
    missing_files = [
        file for file in required_files if not checkExistence(getFullPath(file))
    ]

    if missing_files:
        printMessage(STATUSCODE[0], "Missing Dependencies")
        for file in missing_files:
            print(f"\033[1;31mMissing\033[0m: {file}")

        exit()

    # If all files exist, return successfully
    return


checkDependencies()

############################################################################################
# Load the .env file

load_dotenv()

BROKER = os.getenv("BROKER", "localhost")
PORT = int(os.getenv("PORT", 1883))
USERNAME = os.getenv("MQTT_USER")
PASSWORD = os.getenv("MQTT_PASS")
CLIENT_ID = f"mqtt_client_{uuid.uuid4()}"

############################################################################################
# Load topics.json
with open(topicsFilepath, "r") as json_file:
    MQTT_TOPICS = json.load(json_file)

# Load vmInfo.json
with open(vmInfoFilepath, "r") as envFile:
    vmInfoJSON = json.load(envFile)
    VMINFO = vmInfoJSON.get("VMINFO")
    PATHINFO = vmInfoJSON.get("PATHINFO")
    TESTERINFO = vmInfoJSON.get("TESTERINFO")

TOPICS = MQTT_TOPICS.get("TOPICS")
ROOT = TOPICS.get("root")
BROADCAST = TOPICS.get("broadcast")
TESTER_TOPIC = TOPICS.get("tester_topic")
SUBTOPICS = TOPICS.get("subtopics")

execution_path = directoryPath.normpath(
    PATHINFO.get("WIN_SCRIPT_PATH") if isWin() else PATHINFO.get("LIN_SCRIPT_PATH")
)


############################################################################################


def get_python_path():
    command = "where python" if os.name == "nt" else "which python"
    try:
        result = subprocess.check_output(command, shell=True, universal_newlines=True)
        result = directoryPath.normpath(result.strip())
        return result

    except Exception as error:
        print("Error finding python executable.")
        return None


def get_shell_path():
    command = "where pwsh" if os.name == "nt" else "which bash"
    try:
        result = subprocess.check_output(command, shell=True)
        result = rf"{result.strip()}"
        result = result.replace("'", "")
        result = result[1:]
        return result

    except Exception as error:
        print("Error finding shell path")
        return None


def get_interface_ip(ifname):
    import fcntl
    import struct

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(
        fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack("256s", bytes(ifname[:15], "utf-8")),
        )[20:24]
    )


def get_default_interface():
    gateways = psutil.net_if_addrs()
    for interface, addrs in gateways.items():
        for addr in addrs:
            if addr.family == socket.AF_INET and addr.address != "127.0.0.1":
                return interface
    return None


def get_public_ip():
    command = "curl -s ifconfig.me"
    try:
        result = subprocess.check_output(command, shell=True, encoding="utf-8")
        result = result.strip()
        return result

    except Exception as error:
        print("Error getting public ip")
        return None


def isServer():
    ip_address = get_public_ip()

    for VM in VMINFO:
        for info in VM.get("info"):
            if ip_address in info.get("hosts"):
                return True

    return False


def signal_handler(sig, frame):
    print("\nKeyboard Interrupt Detected! Exiting gracefully...")
    exit()


# Signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)


############################################################################################
# Fetch TESTER Info...


def fetch_tester_info():
    if isWin():
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
    else:
        interface = get_default_interface()
        if interface:
            interface_name = interface
        else:
            interface_name = "eth0"

        ip_address = get_interface_ip(interface_name)
    return getTester(ip_address)


SUBSCRIPTION_TOPICS = [(BROADCAST, 0)]

if isServer():
    SUBSCRIPTION_TOPICS.append((f"{TESTER_TOPIC}/#", 0))
else:
    TESTER = fetch_tester_info()
    SUBSCRIPTION_TOPICS.append((f"{TESTER_TOPIC}/{TESTER}", 0))

############################################################################################
# MQTT METHODS...


def publish_status_update(client, operation, tester):
    status = json.dumps(
        {
            "operation": "status",
            "tester": tester,
            "message": f"{operation.upper()} Operation performed by {tester}",
        }
    )
    client.publish(BROADCAST, status)


def perform_operation(client, operation, tester, message=None):
    global execution_path

    execution_shell = get_shell_path()
    python_path = get_python_path()
    commandList = []

    if operation == "update":
        updater_file = "updater.ps1" if isWin() else "updater.sh"

        if isWin():
            commandList = [execution_shell, "-File", updater_file]
        else:
            commandList = [execution_shell, "-c", updater_file]

    elif operation == "start":
        testname = message.get("testname")
        terminal_command = rf"{python_path} driver.py --testname {testname} --upload y"

        if isWin():
            commandList = [
                "cmd /c start cmd /c",
                terminal_command,
            ]
        else:
            commandList = rf"{execution_shell} linux_invoker.sh {testname}"

    elif operation == "stop":
        terminal_command = rf"{python_path} stopper.py --tester {tester}"

        if isWin():
            commandList = [
                "cmd /c start cmd /c",
                terminal_command,
            ]
        else:
            commandList = rf"{execution_shell} stopper.sh {tester}"

    else:
        print(f"Unknown command: {operation}")
        return

    subprocess.Popen(
        " ".join(commandList) if isWin() else commandList,
        cwd=execution_path,
        shell=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    publish_status_update(client, operation, tester)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(SUBSCRIPTION_TOPICS)


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")


def on_message(client, userdata, msg):
    try:
        message = json.loads(msg.payload)
        tester = message.get("tester")
        operation = message.get("operation")

        if operation and not (operation == "status"):
            print(f"Received Operation: {operation.upper()} by {tester}")
            perform_operation(client, operation, tester, message)

    except Exception as error:
        print(f"Failed to process message: {error}")
        import traceback

        traceback.print_exc()


############################################################################################
# DRIVER CODE...
def main():
    client = mqtt.Client(CLIENT_ID)
    client.username_pw_set(username=USERNAME, password=PASSWORD)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
