# Multi-Agent


## Getting started

Make sure to copy the .env.example file and add your openai key as well as the model base url
```
pip install -r requirements.txt
chainlit run app.py
```

This is only a demonstration of the ACCOUNT usecase of the system.
The system handles 2 usecase: ACCOUNT for account problems and OTHER for other problems
To test the basic flow, ask account related questions like: "Tài khoản tôi không vào được" then follow the bot's instructions

NOTE: The agent_runtime.log contains the results of past experiment