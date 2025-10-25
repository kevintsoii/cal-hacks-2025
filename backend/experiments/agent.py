from uagents import Agent, Bureau, Context, Model, Protocol
 
ethan = Agent(name="ethan", seed="ethan recovery phrase", port=8000, endpoint=["http://127.0.0.1:8000/submit"])
olivia = Agent(name="olivia", seed="olivia recovery phrase", port=8001, endpoint=["http://127.0.0.1:8001/submit"])
liam = Agent(name="liam", seed="liam recovery phrase", port=8002, endpoint=["http://127.0.0.1:8002/submit"])
 
class BroadcastExampleRequest(Model):
    pass
 
class BroadcastExampleResponse(Model):
    text: str
 
proto = Protocol(name="proto", version="1.0")
 
@proto.on_message(model=BroadcastExampleRequest, replies=BroadcastExampleResponse)
async def handle_request(ctx: Context, sender: str, _msg: BroadcastExampleRequest):
    await ctx.send(
        sender, BroadcastExampleResponse(text=f"Hello from {ctx.agent.name}")
    )
 
ethan.include(proto)
olivia.include(proto)
 
@liam.on_interval(period=5)
async def say_hello(ctx: Context):
    status_list = await ctx.broadcast(proto.digest, message=BroadcastExampleRequest())
    ctx.logger.info(f"Trying to contact {len(status_list)} agents.")
 
@liam.on_message(model=BroadcastExampleResponse)
async def handle_response(ctx: Context, sender: str, msg: BroadcastExampleResponse):
    ctx.logger.info(f"Received response from {sender}: {msg.text}")
 
bureau = Bureau(port=8000, endpoint="http://localhost:8000/submit")
bureau.add(ethan)
bureau.add(olivia)
bureau.add(liam)
 
if __name__ == "__main__":
    bureau.run()