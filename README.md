# WEBIDENCE POC - MQTT

## Table of Contents

- [WEBIDENCE POC - MQTT](#webidence-poc---mqtt)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Purpose of the Tool](#purpose-of-the-tool)
  - [Environment](#environment)
  - [Environment Requirements](#environment-requirements)
  - [Technologies Used](#technologies-used)
  - [Dependencies](#dependencies)
  - [Usage](#usage)
    - [Using Arguments](#using-arguments)
    - [Without Arguments](#without-arguments)
  - [Workflow](#workflow)
  - [Execution Flow](#execution-flow)
    - [Server Script (`server.py`)](#server-script-serverpy)
    - [Client Script (`client.py`)](#client-script-clientpy)
  - [Additional Notes](#additional-notes)
    - [Example `.env` File](#example-env-file)
    - [Example `env.json` File](#example-envjson-file)
    - [Example `topics.json` File](#example-topicsjson-file)
  - [Author](#author)

## Introduction

The `WEBIDENCE POC - MQTT` project consists of two Python scripts: `client.py` and `server.py`. These scripts use the MQTT protocol to manage and execute automated tests across different environments and machines.

## Purpose of the Tool

The purpose of this tool is to facilitate the execution and monitoring of automated tests across multiple systems using the MQTT protocol. The client and server scripts allow for centralized management and communication between testing nodes.

## Environment

The tool is designed to run on both Windows and Linux environments, with appropriate adaptations for each operating system.

## Environment Requirements

1.  Python 3.x
    
2.  Required Python libraries (listed in `requirements.txt`):
    
    -   `paho-mqtt==1.6.1`
        
    -   `python-dotenv`
        
3.  `PowerShell` for Windows or `Bash` for Linux.
    
4.  Internet connection for MQTT broker communication.

## Technologies Used

-   **Python**: Main programming language for the scripts.
    
-   **MQTT**: Protocol used for communication between client and server.
    
-   **PowerShell/Bash**: Scripts for executing specific tasks.
    
-   **dotenv**: For loading environment variables from a `.env` file.
    
-   **subprocess**: For executing shell commands.
    
-   **socket**: For network-related tasks.

## Dependencies

The project requires the following dependencies, which can be installed using `pip`:

```sh
pip install paho-mqtt==1.6.1 python-dotenv
```

OR

```sh
pip install -r requirements.txt
```

## Usage

### Using Arguments

You can run the `server.py` script with arguments to directly specify test information or perform an update. The `client.py` script runs without arguments and listens for commands from the server.

**Example Commands:**

```sh
# This explicitly passes the testname argument...
python server.py --testname BASE-XSS-B01-I01-TEST-AR

# This updates the codebase in all VMs...
python server.py --update y
```

### Without Arguments

If no arguments are provided, the server script will prompt the user for input. The client script does not require any arguments and automatically connects to the MQTT broker to listen for instructions.

## Workflow

1.  **Environment Setup**: Ensure all required files and dependencies are present.
    
2.  **Load Environment Variables**: The `.env` file is loaded to get the broker details, port, username, and password.
    
3.  **Client and Server Scripts**: The server script sends commands to clients based on user input or arguments provided. The client script listens for these commands and executes corresponding actions.
    
4.  **Test Execution**: Commands like `start`, `stop`, and `update` trigger specific operations on the client machine.

## Execution Flow

### Server Script (`server.py`)

1.  **Initialize**: Load environment variables and configurations from JSON files.
    
2.  **Connect to MQTT Broker**: Establish connection and set up callbacks.
    
3.  **Command Execution**: Based on user input or arguments, send commands to clients.
    
4.  **Monitor and Control**: Continuously monitor and control test execution.

### Client Script (`client.py`)

1.  **Initialize**: Load environment variables and configurations from JSON files.
    
2.  **Connect to MQTT Broker**: Establish connection and set up callbacks.
    
3.  **Listen for Commands**: Subscribe to relevant topics and listen for commands from the server.
    
4.  **Execute Commands**: Perform operations like starting/stopping tests or updating scripts based on received commands.
    

## Additional Notes

-   Ensure that all required files (`.env`, `credentials/env.json`, `credentials/vmInfo.json`, `credentials/topics.json`) are present and correctly configured.
    
-   The scripts are designed to be OS-agnostic, with specific commands for Windows and Linux.
    
-   Proper error handling and logging mechanisms are in place to ensure smooth execution and debugging.
    

### Example `.env` File

```
BROKER=localhost
PORT=1883
MQTT_USER=username
MQTT_PASS=password
```

### Example `env.json` File

```json
{
  "ENV": {
    "allowedTesters": ["TESTER1", "TESTER2"],
    "testInfo": [
      {
        "category": "CATEGORY1",
        "name": "Test1"
      },
      {
        "category": "CATEGORY2",
        "name": "Test2"
      }
    ],

    "batches": [1, 2, 3],
    "iterations": [1, 2, 3],
    "testtype": ["PRIVATE", "PUBLIC", "SMOKE", "TEST"]
  },
  "VENDORS": [
    {
      "code": "VENDOR1",
      "name": "Vendor 1"
    },
    {
      "code": "VENDOR2",
      "name": "Vendor 2"
    }
  ]
}
```

### Example `topics.json` File

```json
{
  "TOPICS": {
    "root": "root/topic",
    "broadcast": "broadcast/topic",
    "tester_topic": "tester/topic",
    "subtopics": ["subtopic1", "subtopic2"]
  }
}
```

## Author
[Aayush Rajthala](https://github.com/AayushRajthala99)

Ensure all paths in the configuration files are correct and accessible from your scripts.

---
