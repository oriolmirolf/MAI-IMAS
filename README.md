# Multi-Agent Emergency Response System

This project simulates a city's emergency response to fire incidents using a multi-agent system (MAS). Built on top of the CrewAI framework, it orchestrates a series of autonomous agents who collaborate to generate an optimal plan for extinguishing fires and transporting injured individuals to the nearest hospitals. 

The system processes an emergency call transcript, distills the key information (e.g., fire type, severity, location, and number of injured individuals), and coordinates fire crews and medical crews to plan and execute rescue operations. The resulting output is a clear, human-readable Markdown report justifying each decision made by the agents.

---

## Table of Contents
1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Prerequisites and Installation](#prerequisites-and-installation)
4. [Usage](#usage)
5. [Key Components](#key-components)
    1. [Emergency Services Crew](#emergency-services-crew)
    2. [Firefighter Crew](#firefighter-crew)
    3. [Medical Services Crew](#medical-services-crew)
    4. [Reporter Crew](#reporter-crew)
6. [Custom Tools](#custom-tools)
7. [Report and Documentation](#report-and-documentation)
8. [Authors](#authors)

---

## Overview

### Why a Multi-Agent System?
Coordinating fire response and medical assistance in real time requires multiple specialized tasks to be performed in parallel (fire containment, evacuation, patient triage, etc.). A multi-agent approach, where each agent is specialized in a particular domain (e.g., route navigation, medical triage, resource allocation), is well-suited to capture the complexity of such emergencies.

### Project Goals
- **Fire Management**: Determine the type of fire, required personnel, vehicles, and optimal routes to the location.
- **Medical Services**: Evaluate patient injuries, allocate ambulances, and assign hospital rooms.
- **Plan Justification**: Explain decisions (why a particular resource was chosen, how the route was selected, etc.) to aid in system transparency and allow human operators to identify mistakes.

---

## Project Structure

```bash
project/
├── docs/
│   └── report.pdf          # Detailed documentation and final report
├── requirements.txt        # Python dependencies for the MAS
├── src/
│   └── project/
│       ├── crews/
│       │   ├── emergency_crew/
│       │   │   ├── emergency_crew.py
│       │   │   └── ...
│       │   ├── fire_crew/
│       │   │   ├── fire_crew.py
│       │   │   └── ...
│       │   ├── medical_crew/
│       │   │   ├── medical_crew.py
│       │   │   └── ...
│       │   └── reporter_crew/
│       │       ├── reporter_crew.py
│       │       └── ...
│       ├── maps/
│       │   └── vilanova_i_la_geltru.graphml  # Graph representation of the city map
│       └── tools/
│           ├── fire_crew_navigator_tool.py
│           ├── ambulance_selector_tool.py
│           ├── hospital_selector_tool.py
│           └── route_navigator_tool.py
├── test/
│   ├── test1.txt
│   ├── test2.txt
│   └── test3.txt
└── outputs/
    ├── output1.txt
    ├── output2.txt
    └── output3.txt
```

- `docs/`: Contains the project’s detailed final report.
- `requirements.txt`: Dependencies and Python libraries needed to run the MAS.
- `src/project/crews/`: Each crew (emergency, fire, medical, reporter) has its own folder containing YAML configuration files, agent definitions, and any related utility code.
- `src/project/maps/`: GraphML map file(s) used for route calculations.
- `src/project/tools/`: Custom tool implementations for file reading, ambulance selection, hospital assignment, route navigation, etc.
- `test/`: Sample input files that simulate emergency calls.
- `outputs/`: Contains the final Markdown outputs (i.e., the system’s plan and justification) for each test input.

---

## Prerequisites and Installation
1. Clone the repository (if applicable) or download it as a ZIP and extract it locally.
2. Install Python 3.9+ (recommended) or a compatible version.
3. Navigate to the project root (where `requirements.txt` is located).
4. Install dependencies:
```
pip install -r requirements.txt
```

---

## Usage
1. Navigate to the `project/` folder:
```
cd project

```

2. Execute the flow:
```
crewai flow kickoff
```

3. View Output:
- After execution, results are saved as `.txt` files in `outputs/`.
- For example, `output1.txt` is generated after running `test1.txt`.

You can review these text files to see the entire plan the system has produced, along with the justifications provided by each agent.

---

## Key Components

### Emergency Services Crew
- **Purpose**: Reads the initial emergency call transcript (e.g., `test1.txt`), extracts critical information (fire type, location, injuries), and structures it using a Pydantic schema.  
- **Highlights**:
  - A single **Distiller Agent** processes raw text to reduce hallucinations and simplify the data pipeline.  
  - Outputs validated data (severity, number of injured, location, etc.) for the Fire and Medical Crews.

### Firefighter Crew
- **Purpose**: Orchestrates fire response planning, including:
  1. **Fire Expert Agent**: Recommends an ideal plan (personnel, vehicles, materials) to fight the fire.
  2. **Material Selector Agent**: Adjusts the ideal plan based on actual resources available at the fire station.
  3. **Material Navigator Agent**: Computes the optimal route from the fire station to the fire location using the **FireCrewNavigatorTool**.
  4. **Firefighter Planner**: Consolidates all outputs into a final structured plan (e.g., number of firefighters, route, estimated time).
- **Output**: A structured **FirefighterPlannerSchema** (Pydantic) that other crews or the reporter can interpret.

### Medical Services Crew
- **Purpose**: Evaluates injuries and plans medical assistance, including:
  1. **Emergency Doctor Agent**: Assesses each patient’s medical condition (nurse check, hospitalization, ICU).
  2. **Ambulance Selector Agent**: Chooses the most suitable ambulances based on proximity and capacity, using **AmbulanceSelectorTool**.
  3. **Hospital Assigner Agent**: Assigns patients and ambulances to specific hospitals/rooms, using **HospitalSelectorTool**.
  4. **Route Navigator Agent**: Calculates routes from ambulance location to fire scene, and then from fire scene to the assigned hospital, via **RouteNavigatorTool**.
  5. **Medical Planner**: Consolidates the decisions into a single plan (which ambulances, which hospitals, final routes, etc.).
- **Output**: A **MedicalPlannerSchema** summarizing ambulance usage, hospital allocations, route details, and justification.

### Reporter Crew
- **Purpose**: Transforms the final JSON outputs (combining both Firefighter and Medical Crew plans) into a human-readable Markdown report.
- **Process**:
  1. **Writer Agent**: Converts the dense JSON plan into a schematic Markdown.
  2. **Formatter Agent**: Improves the document structure, adds context, and ensures each decision is properly explained.
- **Focus on Explainability**: Every plan element (e.g., “Why did we pick this ambulance?”) is justified so a human can easily identify and correct errors if needed.

---

## Custom Tools
- **FileReadTool**: Standardized utility for reading emergency transcripts from `test/`.
- **AmbulanceSelectorTool**: Ranks ambulances by distance to the fire scene, considering availability and capacity.
- **HospitalSelectorTool**: Assigns patients to hospitals with available rooms (normal or ICU), factoring in location proximity and severity of injuries.
- **FireCrewNavigatorTool** & **RouteNavigatorTool**: Compute optimal paths using map data (e.g., a `.graphml` file) to find the quickest or safest routes.  

Using these tools offloads computational logic from the language-model agents, reducing hallucinations and errors.

---

## Report and Documentation
- A detailed **report** describing the system architecture, implementation details, and experimental setup can be found in the `docs/` folder.
- **Test Inputs and Outputs**:
  - **Inputs**: Located in the `test/` folder (`test1.txt`, `test2.txt`, `test3.txt`).
  - **Outputs**: Generated Markdown files in the `outputs/` folder (e.g., `output1.txt`).

---

## Authors
- **Joan Caballero Castro** (GitHub: [@JoanK11](https://github.com/JoanK11))
- **Oriol Miró López-Feliu** (GitHub: [@oriolmirolf](https://github.com/oriolmirolf))
- **Marc Gonzalez Vidal** (GitHub: [@Gonsa02](https://github.com/Gonsa02))
- **Julia Amenós Dien** (GitHub: [@juliia-ad](https://github.com/juliia-ad))
- **Víctor Carballo Araruna** (GitHub: [@Vicara12](https://github.com/Vicara12))

We hope this multi-agent emergency response system proves illustrative of how AI-driven agents can collaborate in complex real-world scenarios like firefighting and medical rescue. If you have any questions or suggestions, please feel free to reach out via the authors’ GitHub profiles.
