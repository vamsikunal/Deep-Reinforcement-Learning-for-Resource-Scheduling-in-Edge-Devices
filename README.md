# Deep Reinforcement Learning for Resource Scheduling in Edge Devices

This project implements a Deep Reinforcement Learning (DRL) based approach, specifically Deep Deterministic Policy Gradient (DDPG), to optimize resource scheduling and bandwidth allocation in Mobile Edge Computing (MEC) environments.

## Overview

In the era of IoT and 5G, massive heterogeneous industrial devices communicating with clouds can lead to high latency and network congestion. Edge computing mitigates these issues by processing data closer to the source. However, edge devices have limited resources. This project leverages DDPG to dynamically allocate computing power and network bandwidth, ensuring efficient task offloading and migration for mobile users.

The system models a multi-user heterogeneous network with Micro Edge Stations (MES) and mobile devices. It handles:
- **Task Offloading:** Deciding which edge server a user should offload their task to.
- **Resource Allocation:** Allocating computational resources (CPU) to connected users.
- **Bandwidth Allocation:** Managing bandwidth for task migration between edge servers.
- **User Mobility:** Simulating user movement using real-world traces (CRAWDAD dataset).

## Features

- **Deep Deterministic Policy Gradient (DDPG):** Utilizes an Actor-Critic architecture with Twin Q-Networks for stable and efficient continuous control.
- **Dynamic Environment:** Adapts to changing user locations and resource demands in real-time.
- **Mobility Support:** Incorporates user mobility patterns to trigger task migration between edge servers.
- **Multi-Dimensional Action Space:** Simultaneously optimizes offloading decisions, resource allocation, and bandwidth allocation.
- **Performance Visualization:** Includes plotting tools to visualize rewards and variance over training episodes.

## Installation

To run this project, you need Python installed along with the following dependencies:

```bash
pip install tensorflow numpy matplotlib
```

*Note: The code is designed to work with TensorFlow 1.x or TensorFlow 2.x with v1 compatibility enabled.*

## Usage

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd Deep-Reinforcement-Learning-for-Resource-Scheduling-in-Edge-Devices
    ```

2.  **Run the simulation:**
    ```bash
    python main.py
    ```

    The `main.py` script initializes the environment and the DDPG agent, then starts the training loop.

3.  **Output:**
    - Training logs and results are saved in the `output/` directory.
    - Plots for rewards (`rewards.png`) and variance (`variance.png`) are generated after the simulation completes.
    - A record file (`record.txt`) contains detailed simulation parameters and results.

## Project Structure

- `main.py`: The entry point of the application. Handles the training loop, parameter initialization, and result plotting.
- `DDPG.py`: Implements the DDPG algorithm, including the Actor and Critic networks, replay buffer, and training logic.
- `env.py`: Defines the MEC environment (`Env` class), including:
    - `UE`: User Equipment (Mobile User) class handling mobility and request generation.
    - `EdgeServer`: Edge Server class managing resources and connections.
    - `Request`: Class representing a task offloading request.
    - `TaskType`: Defines task characteristics (e.g., data size, processing requirements).
- `data/`: Contains the mobility traces (CRAWDAD dataset) used for simulation.
