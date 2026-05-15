from fastapi import FastAPI
from agent import ask_agent, AgentResponse

app = FastAPI(title="Fitness Trainer API")


class AskRequest(AgentResponse):
    pass



@app.post("/ask", response_model=AgentResponse)
def ask(query: str):
    return ask_agent(query)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)