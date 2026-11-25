answers = {"hello": "Hi!", "what is your name": "I am a bot."}

question = input("Ask: ").lower().strip("?! ")
print(answers.get(question, "?"))
