from agent.agent import Agent

agent = Agent()

while True:
    user_input = input("\n> ")

    if user_input.lower() in ["exit", "quit"]:
        break

    agent.run(user_input)