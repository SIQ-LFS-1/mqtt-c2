import os
import json
import time
import uuid
import argparse
from pythonping import ping
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


def getNormalizedPath(pathvalue):
    return directoryPath.normpath(pathvalue)


def getFullPath(pathValue):
    return getNormalizedPath(directoryPath.abspath(pathValue))


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


def isMQTTServerUp(host):
    response = ping(host, count=3)
    if response.success():
        return True
    else:
        return False


############################################################################################
# Checking Dependencies...


def checkDependencies(required_files):
    clear_screen()

    # Check for the existence of each required file
    missing_files = [file for file in required_files if not checkExistence(file)]

    if missing_files:
        printMessage(STATUSCODE[0], "Missing Dependencies")
        for file in missing_files:
            print(f"\033[1;31mMissing\033[0m: {file}")

        exit()

    # If all files exist, return successfully
    return


############################################################################################
# Load the .env file
load_dotenv()

BROKER = os.getenv("BROKER", "localhost")
PORT = int(os.getenv("PORT", 1883))
USERNAME = os.getenv("MQTT_USER")
PASSWORD = os.getenv("MQTT_PASS")
CLIENT_ID = f"mqtt_client_{uuid.uuid4()}"

SCRIPT_PATH = os.getenv("WIN_SCRIPT_PATH") if isWin() else os.getenv("LIN_SCRIPT_PATH")

if "/" == SCRIPT_PATH[-1]:
    SCRIPT_PATH = SCRIPT_PATH[:-1]

############################################################################################
# Assigning filepaths to a variable...

envFilepath = getNormalizedPath(rf"{SCRIPT_PATH}/.env")
envjsonFilepath = getNormalizedPath(rf"{SCRIPT_PATH}/credentials/env.json")
vmInfoFilepath = getNormalizedPath(rf"{SCRIPT_PATH}/credentials/vmInfo.json")
topicsFilepath = getNormalizedPath(rf"{SCRIPT_PATH}/credentials/topics.json")

# Define all required files
required_files = [envFilepath, envjsonFilepath, vmInfoFilepath, topicsFilepath]

checkDependencies(required_files)

############################################################################################
# Load env.json
with open(envjsonFilepath) as json_file:
    env_config = json.load(json_file)

ALLOWED_TESTERS = env_config["ENV"]["allowedTesters"]
TEST_INFO = env_config["ENV"]["testInfo"]
VENDORS = env_config["VENDORS"]
BATCHES = env_config["ENV"]["batches"]
ITERATIONS = env_config["ENV"]["iterations"]
TEST_TYPES = env_config["ENV"]["testtype"]


############################################################################################
# Load topics.json
with open(topicsFilepath, "r") as json_file:
    MQTT_TOPICS = json.load(json_file)

TOPICS = MQTT_TOPICS["TOPICS"]
ROOT = TOPICS["root"]
BROADCAST = TOPICS["broadcast"]
TESTER_TOPIC = TOPICS["tester_topic"]
SUBTOPICS = TOPICS["subtopics"]

############################################################################################
# FUNCTIONS DECLARATIONS...


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Successfully Connected to the MQTT Server!")
        client.subscribe((BROADCAST, 0))

    else:
        if rc == 1:
            print("Connection Failed : unacceptable protocol version.")
        elif rc == 2:
            print("Connection Failed : identifier rejected.")
        elif rc == 3:
            print("Connection Failed : server unavailable.")
        elif rc == 4:
            print("Connection Failed : bad username or password.")
        elif rc == 5:
            print("Connection Failed : not authorized.")
        else:
            print(f"Connection Failed with unknown error code: {rc}")


def on_disconnect(client, userdata, rc):
    if rc == 0:
        print("Successfully Disconnected from the MQTT Server!")
    elif rc == 1:
        print("Unexpected Disconnection : Protocol error.")
    elif rc == 2:
        print("Unexpected Disconnection : Network issue.")
    elif rc == 3:
        print("Unexpected Disconnection : Client disconnected by broker.")
    elif rc == 4:
        print("Unexpected Disconnection : Bad username or password.")
    elif rc == 5:
        print("Unexpected Disconnection : Not authorized.")
    else:
        print(f"Unexpected Disconnection : Unknown reason [ Return code: {rc} ]")


def on_message(client, userdata, msg):
    try:
        message = json.loads(msg.payload)
        print(f"Received message: {message}")
    except Exception as error:
        printMessage(STATUSCODE[0], "Failed to process message")
        import traceback

        traceback.print_exc()


def on_publish(client, userdata, mid):
    print("\nMessage Published")


def perform_update(client):
    try:
        global BROADCAST
        msg = json.dumps({"operation": "update"})
        client.publish(BROADCAST, msg)

    except Exception as error:
        printMessage(STATUSCODE[0], "Failed to publish command")


def publish_command(client, operation, tester, testname=None):
    try:
        if operation == "start":
            msg = json.dumps(
                {"operation": operation, "testname": testname, "tester": tester}
            )

        elif operation == "stop":
            msg = json.dumps({"operation": operation, "tester": tester})

        TOPIC = f"{TESTER_TOPIC}/{tester}"
        client.publish(TOPIC, msg)

    except Exception as error:
        printMessage(STATUSCODE[0], "Failed to publish command")


def getUserInput():
    clear_screen()
    print("\nENTER TEST INFORMATION:")

    while True:
        # Input for tester
        tester = input("\nInput Tester ID >>> ").strip().upper()
        if tester not in ALLOWED_TESTERS:
            print("\nInvalid Tester. Please choose from:", ", ".join(ALLOWED_TESTERS))
            exit()

        clear_screen()

        # Input for Test Category
        print(f"\nTEST CATEGORY:\n")
        test_categories = sorted(set(test["category"] for test in TEST_INFO))
        for index, name in enumerate(test_categories, start=1):
            print(f"{index}. {name}")

        try:
            test_category_id = int(input("\nInput Test Category >>> ").strip())
            test_category_value = test_categories[(test_category_id - 1)]
        except Exception as error:
            printMessage(STATUSCODE[0], "Invalid Test Category")
            exit()

        if test_category_value != "FALSE-POSITIVE":
            try:
                if (
                    (test_category_value == "LAYER7-DOS")
                    or (test_category_value == "BOT-ATTACKS")
                    or (test_category_value == "APPLICATION-SCANNING-ATTACKS")
                ):

                    filterValue = ""

                    if test_category_value == "LAYER7-DOS":
                        filterValue = "LAYER7-DOS"

                    elif test_category_value == "APPLICATION-SCANNING-ATTACKS":
                        filterValue = "APPLICATION-SCANNING-ATTACKS"

                    else:
                        filterValue = "BOT-ATTACKS"

                    TEST_NAMES = next(
                        (
                            item["subtests"]
                            for item in TEST_INFO
                            if item.get("category") == filterValue
                        ),
                        None,
                    )

                else:
                    TEST_NAMES = sorted(
                        [
                            test["name"]
                            for test in TEST_INFO
                            if test["category"] == test_category_value
                        ]
                    )

                clear_screen()

            except Exception as error:
                printMessage(STATUSCODE[0], "TEST INFO PARSE ERROR")
                exit()

            print(f"\nTEST NAMES:\n")
            for index, name in enumerate(TEST_NAMES, start=1):
                print(f"{index}. {name}")

            try:
                test_code_value = int(input("\nInput Test Code >>> ").strip())
                test_category = TEST_NAMES[(test_code_value - 1)]
            except Exception as error:
                printMessage(STATUSCODE[0], "Invalid Test Code")
                # print(error)
                exit()
        else:
            test_category = "FP"

        clear_screen()

        # Input for Vendor
        print(f"\nVENDOR LIST:\n")
        for index, vendor in enumerate(VENDORS, start=1):
            print(f"{index}. {vendor['name']}")

        try:
            vendorid = int(input("\nInput Vendor ID (e.g. 1, 2) >>> "))
            vendorcode = VENDORS[(vendorid - 1)]["code"]
            vendorname = VENDORS[(vendorid - 1)]["name"]
        except Exception as error:
            printMessage(STATUSCODE[0], "Invalid Vendor Selected")
            exit()

        clear_screen()

        # Input for test type
        test_type = (
            input("\nInput Test Type (e.g. PRIVATE, PUBLIC, SMOKE, TEST) >>> ")
            .strip()
            .upper()
        )
        if test_type not in TEST_TYPES:
            print("\nInvalid Test Type. Please choose from:", ", ".join(TEST_TYPES))
            exit()

        clear_screen()

        try:
            # Input for batch
            batch = int(input("\nInput Batch Number (e.g. 1, 2, 3) >>> ").strip())
            if batch > 0 and batch < 10:
                batch = f"B0{batch}"
            else:
                batch = f"B{batch}"
        except Exception as error:
            printMessage(STATUSCODE[0], "Invalid Batch Number")
            exit()

        clear_screen()

        try:
            # Input for iteration
            iteration = int(
                input("\nInput Iteration Number (e.g. 1, 2, 3) >>> ").strip()
            )
            if iteration > 0 and iteration < 10:
                iteration = f"I0{iteration}"
            else:
                iteration = f"I{iteration}"
        except Exception as error:
            printMessage(STATUSCODE[0], "Invalid Iteration Number")
            exit()

        clear_screen()

        # Input accepted, print the information
        print("\nInformation entered:\n")
        print("Tester >>> ", tester)
        print("Vendor >>> ", vendorname)
        print("Test Category >>> ", test_category)

        print("\nTest Name >>> ", end="")
        if len(test_type) > 0:
            test_name = (
                f"{vendorcode}-{test_category}-{batch}-{iteration}-{test_type}-{tester}"
            )
        else:
            test_name = f"{vendorcode}-{test_category}-{batch}-{iteration}-{tester}"

        print(test_name)

        # Ask if user wants to continue
        choice = input("\nDo you want to continue (yes/no)? >>> ").strip().lower()
        if choice in ["yes", "y"]:
            return [tester, test_name]
        else:
            clear_screen()
            printMessage(STATUSCODE[1], "TEST INFORMATION DISCARDED")


def main():
    global BROKER

    ############################################################################################
    # MQTT Connection...
    try:
        printMessage(STATUSCODE[1], "Connecting to MQTT Server")

        client = mqtt.Client(CLIENT_ID)
        client.username_pw_set(username=USERNAME, password=PASSWORD)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_publish = on_publish
        client.on_message = on_message
        client.connect(BROKER, PORT, 60)
        client.loop_start()

        time.sleep(2)
        clear_screen()

    except TimeoutError:
        printMessage(STATUSCODE[0], "Connection Timed Out")
        printMessage(STATUSCODE[1], "Checking Status of MQTT Server. Please Wait!")

        if isMQTTServerUp(BROKER):
            printMessage(STATUSCODE[1], "MQTT Server is ONLINE")
        else:
            printMessage(STATUSCODE[1], "MQTT Server is OFFLINE")

        exit()

    except Exception as error:
        printMessage(STATUSCODE[0], error)
        exit()

    ############################################################################################
    # GLOBAL INPUT VARIABLES...

    parser = argparse.ArgumentParser(description="WEBIDENCE-MQTT")

    # Argument parser for testname, Ex:BASE-XSS-B01-I01-TEST-AR
    parser.add_argument("--testname", type=str, help="Test name")

    # Argument parser for update operation
    parser.add_argument(
        "--update",
        action="store_const",
        default=False,
        const=True,
        help="Global Update",
    )

    args = parser.parse_args()

    TESTNAME = args.testname
    UPDATE = args.update

    # Validating arguments...
    if UPDATE:
        try:
            perform_update(client)

        except Exception as error:
            print(error)
            pass

    else:
        try:
            # Validating arguments...
            if TESTNAME:
                try:
                    TESTER = TESTNAME.split("-")[-1]

                except Exception as error:
                    TESTER = "TEST"
                    pass
            else:
                TESTER, TESTNAME = getUserInput()

            OPERATION = "start"
            publish_command(client, OPERATION, TESTER, TESTNAME)

            print("--INFO--[ TEST IN PROGRESS ]")

            while True:
                clear_screen()
                print("--INFO--[ TEST IN PROGRESS ]")

                # Ask if user wants to stop...
                choice = input("\nDo you want to stop (y/n)? >>> ").strip().lower()
                if choice == "yes" or choice == "y":
                    choice = input("\nAre you sure (y/n)? >>> ").strip().lower()
                    if choice == "yes" or choice == "y":
                        OPERATION = "stop"
                        publish_command(client, OPERATION, TESTER)
                        break

            successBanner()

        except KeyboardInterrupt:
            print("\nKeyboard Interrupt Detected! Exiting gracefully...")
            OPERATION = "stop"
            publish_command(client, OPERATION, TESTER)

        except Exception as error:
            printMessage(STATUSCODE[0], error)

        finally:
            client.loop_stop()
            client.disconnect()

            print("\nCleaning-Up Resources & Exiting gracefully...")


if __name__ == "__main__":
    main()
