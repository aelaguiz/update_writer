# Amir's personal RAG


Connects to google drive, gmail, slack. Slack pretty busted.

You need to have:

- Access to an API Secret for your Google Or
- A postgres database instance with pgvector installed (don't worry about schema it'll create it) 
- An openai API key


## Roadmap

1. Automatic updating of docs & e-mails
1. Make retrieval aware of document names
2. Standardize metadata format across file tylpes
3. Pull document loading into its own library
4. Make personal GPT aware of the type of request and decide which things it should do (doc retrieval, etc)