import asyncio
from mavsdk import System
from mavsdk.mission import (Mission, MissionItem, MissionPlan)
from geopy.geocoders import Nominatim
from operator import itemgetter

geolocator = Nominatim(user_agent="Vriksh Flight Systems")

def get_category_from_choice(choice):
    #TODO: Add exception handling
    switcher = {
        "1": "Food",
        "2": "Medicine",
        "3": "Clothes",
        "4": "Household supplies",
        "5": "Essential supplies",
        "6": "Other recreational supplies"
    }
    category = switcher.get(choice)
    print(f"You chose to order {category}.")
    return category

def get_priority_from_choice(choice):
    # TODO: Add exception handling
    category = get_category_from_choice(choice)
    switcher = {
    "Food": "Moderate",
    "Medicine": "High",
    "Clothes": "Low",
    "Household supplies": "Moderate",
    "Essential supplies": "High",
    "Other recreational supplies": "Low"
    }
    priority = switcher.get(category)
    print(f"The priority of the delivery has been set to {priority}.\n")
    return priority

def get_delivery_priority():
    print("\t1. Food\n\
        2. Medicine\n\
        3. Clothes\n\
        4. Household supplies\n\
        5. Essential supplies\n\
        6. Other recreational supplies\n")
    choice = input("From the menu above, choose a category for your delivery: ")
    priority = get_priority_from_choice(choice)
    return priority

def get_delivery_latitude_longitude():
    try:
        address = input("Enter an address for delivery: ")
        location = geolocator.geocode(address)
        print(location.address)
        lat, lng = location.latitude, location.longitude
        print(lat, lng)
    except:
        lat, lng = None, None
    return lat, lng

async def run():
    drone = System()
    # await drone.connect("serial:///dev/tty.usbmodem01:57600") 
    await drone.connect(system_address="udp://:14540")

    deliveries = []
    proceed = "Y"
    while (proceed=="Y" or proceed=="y"):
        delivery_priority = get_delivery_priority()
        lat, lng = get_delivery_latitude_longitude()
        deliveries.append([delivery_priority, [lat, lng]])
        proceed = input("\nDo you wish to add more deliveries? (Y/N): ")

    # print("\nDelivery information:")
    # for delivery in deliveries:
    #     print(delivery)

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"Drone discovered with UUID: {state.uuid}")
            break

    print_mission_progress_task = asyncio.ensure_future(print_mission_progress(drone))

    running_tasks = [print_mission_progress_task]
    termination_task = asyncio.ensure_future(observe_is_in_air(drone, running_tasks))

    high = [delivery for delivery in deliveries if delivery[0]=="High"]
    moderate = [delivery for delivery in deliveries if delivery[0]=="Moderate"]
    low = [delivery for delivery in deliveries if delivery[0]=="Low"]
    deliveries = high + moderate + low
    deliveries = list(filter(None, deliveries))

    mission_items = []
    for destination in deliveries:
        print(destination)
        lat, lng = destination[1][0], destination[1][1]
        mission_items.append(MissionItem(lat,
                                         lng,
                                         25,
                                         10,
                                         True,
                                         float('nan'),
                                         float('nan'),
                                         MissionItem.CameraAction.NONE,
                                         float('nan'),
                                         float('nan')))

    mission_plan = MissionPlan(mission_items)

    await drone.mission.set_return_to_launch_after_mission(True)

    # print("-- Clearing previous missions")
    # await drone.mission.clear_mission()
    await asyncio.sleep(2)
    print("-- Uploading mission")
    await drone.mission.upload_mission(mission_plan)

    print("-- Arming")
    await drone.action.arm()

    print("-- Starting mission")
    await drone.mission.start_mission()

    await termination_task

async def print_mission_progress(drone):
    async for mission_progress in drone.mission.mission_progress():
        print(f"Mission progress: "
              f"{mission_progress.current}/"
              f"{mission_progress.total}")

async def observe_is_in_air(drone, running_tasks):
    """ Monitors whether the drone is flying or not and
    returns after landing """

    was_in_air = False

    async for is_in_air in drone.telemetry.in_air():
        if is_in_air:
            was_in_air = is_in_air

        if was_in_air and not is_in_air:
            for task in running_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            await asyncio.get_event_loop().shutdown_asyncgens()

            return

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())