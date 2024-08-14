import os
import json
import time
import uuid
import signal
import argparse
import threading
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
    required_files = [envjsonFilepath, vmInfoFilepath, topicsFilepath]

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
    print("Connected with result code " + str(rc))
    client.subscribe((BROADCAST, 0))


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")


def on_message(client, userdata, msg):
    try:
        message = json.loads(msg.payload)
        print(f"Received message: {message}")
    except Exception as error:
        print(f"Failed to process message: {error}")
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
        print(f"Failed to publish command: {error}")


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
        print(f"Failed to publish command: {error}")


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
            print(f"--[ ERROR ]--[ Invalid Test Category ]\n")
            exit()

        if test_category_value != "FALSE-POSITIVE":
            try:
                if test_category_value in [
                    "LAYER7-DOS",
                    "BOT-ATTACKS",
                    "APPLICATION-SCANNING-ATTACKS",
                ]:
                    filter_value = test_category_value

                    TEST_NAMES = next(
                        (
                            item["subtests"]
                            for item in TEST_INFO
                            if item.get("category") == filter_value
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
                print(f"--[ ERROR ]--[ TEST INFO PARSE ERROR ]\n")
                exit()

            print(f"\nTEST NAMES:\n")
            for index, name in enumerate(TEST_NAMES, start=1):
                print(f"{index}. {name}")

            try:
                test_code_value = int(input("\nInput Test Code >>> ").strip())
                test_category = TEST_NAMES[(test_code_value - 1)]
            except Exception as error:
                print(f"--[ ERROR ]--[ Invalid Test Code ]\n")
                print(error)
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
            print(f"--[ ERROR ]--[ Invalid Vendor Selected ]\n")
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
            print(f"--[ ERROR ]--[ Invalid Batch Number ]\n")
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
            print(f"--[ ERROR ]--[ Invalid Iteration Number ]\n")
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
            print("\n--[ INFO ]--[ TEST INFORMATION DISCARDED ]\n")
            exit()


def main():
    ############################################################################################
    # MQTT Connection...
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

        finally:
            client.loop_stop()
            client.disconnect()

            print("\nCleaning-Up Resources & Exiting gracefully...")


if __name__ == "__main__":
    main()
