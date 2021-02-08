import asyncio
from mavsdk import System

async def run():

    drone = System()
    # await drone.connect()
    await drone.connect("serial:///dev/tty.usbmodem01:115200")
    # await drone.connect("udp://192.168.43.1:14550")
    # await drone.connect("tcp://0.0.0.0:5760")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"Drone discovered with UUID: {state.uuid}")
            break
    
    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok:
            print("Global position estimate ok")
            break

    print("-- Arming")
    await drone.action.arm()

    print("-- Taking off")
    await drone.action.takeoff()

    await asyncio.sleep(10)

    print("-- Landing")
    await drone.action.land()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())