# KRPC2 Autonomous Mission AI

## Overview

KRPC2 is an AI-powered, autonomous flight system for Kerbal Space Program using GPT-2 and reinforcement-inspired logic to execute launch sequences, orbit insertion, and early-stage mission control.

## Features

- GPT-2 model ensemble for AI-driven decisions

- Full KRPC vessel integration

- Intelligent stage analysis and activation

- Orbit targeting and dynamic control

- Logging system and shutdown signal handling

## Requirements

```plaintext
krpc
torch>=1.10.0
transformers>=4.0.0
```

## How to Run

1. Start the KRPC server in KSP.

2. Ensure the vessel is launch-ready.

3. Run the script:

   ```bash
   python krpc2_main.py
   ```

4. Monitor the console or check `oberon_log.txt` for status.

## Notes

- GPT-2 models vote on actions based on environment context.

- Mission phases currently include Launch and Orbit Circularization.

- Built-in signal handlers allow graceful shutdown (Ctrl+C).

## Future Ideas

- Extend AI decision layers with custom rewards

- Add landing support and interplanetary planning

- Train custom GPT-2 on KSP telemetry logs
