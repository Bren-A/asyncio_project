#!/usr/bin/env python3

# kill $(lsof -t -i:12345)

import asyncio
import time, datetime
import aiohttp
import json
import pprint
import sys

IP_ADDR = '127.0.0.1'

# API key
key = 'AIzaSyBilR_bODNKMrYLnTYozcW6-6e7K37VoxM'

# Port allocations
ports = {
    'Goloman':11465, 
    'Hands':11466, 
    'Holiday':11467, 
    'Welsh':11468, 
    'Wilkes':11469
}

# Which servers each server can communicate to
send_to = {
    'Goloman' : ['Hands', 'Holiday', 'Wilkes'],
    'Hands' : ['Wilkes', 'Goloman'],
    'Holiday' : ['Welsh', 'Wilkes', 'Goloman'],
    'Welsh' : ['Holiday'], 
    'Wilkes' : ['Goloman', 'Hands', 'Holiday']
}

# Initial list of clients
# Format = 'client_name' : [location, time_updated, server]
clients = {}

# Function that gets current time in string format
def current_time():
    return str(time.mktime(datetime.datetime.now().timetuple()))


"""
class MyServer:
    def __init__(self, name, ip, p):
        self.server_name = name
        self.ip_addr = ip
        self.port = p
        
    async def start_server(self):    
        self.server = await asyncio.start_server(handle_connection, host = self.ip_addr, port = self.port)
        await self.server.serve_forever()
"""

# Tries to parse a latitude and longitude value
def get_coord(coord):
    # Check the amount of sign values
    # Sign values must be 2 else wrong formatting
    signs = []
    for i in range(0,len(coord)):
        # If it is a sign add index to list
        if coord[i] == '-' or coord[i] == '+':
            signs.append(i)

    # Check if there are only 2 signs
    # And the first sign shows up at the beginning
        # i.e. No extra symbols at the start
    # Check second sign is not last one
        # Makes sure there are values for second sign(not blank)
    if len(signs) != 2 \
    or signs[0] != 0 \
    or signs[1] == len(coord) - 1:
        # If false for any of these return None
        return "FAIL"
    # Check that both values are floats
    try:
        float(coord[:signs[1]]) + float(coord[signs[1]:])
    except:
        return "FAIL"
    # If they are return a string separating the two
    return str(coord[:signs[1]]) + ',' + str(coord[signs[1]:])


#print(get_coord('+12345-53324'))

# Checks input to see which option is chosen
# 1 == IAMAT, 2 == WHATSAT, -1 == neither
def check_input(string):
    new_str = string.split()
    if not (len(new_str) == 4):
        return -1
    elif new_str[0] == 'IAMAT':
        # Check if the latitude/longitude is valid
        if get_coord(new_str[2]) == 'FAIL':
            return -1
        else:
            # See if the time is a valid time
            try:
                float(new_str[3])
                # If it is return 1
                return 1
            # If not possible return -1
            except:
                return -1

    elif new_str[0] == 'WHATSAT':
        # Check if the radius and entries are valid
        # Make sure the radius is a float
        # Set the value to radius, if possible
        try:
            radius = float(new_str[2])
        # If not possible return -1
        except:
            return -1
        # Check if within valid range
        if radius > 50 or radius <= 0:
            return -1
        # If it is, check if number of entries is valid
        else:
            # Try to assign an into to num_entries
            try:
                num_entries = int(new_str[3])
            # If not int return -1
            except:
                return -1
            # See if num has correct range
            if num_entries > 20 or num_entries <= 0:
                return -1
            else:
                return 2
    else:
        return -1

#print(check_input('IAMAT a +1234-4567 30.0'))

async def get_items_around(location,radius, items):
    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=%s&radius=%d&key=%s' % (location,radius,key)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            results = await resp.json()
            # Modify results to only have first [items] amount
            results['results'] = results['results'][:items]
            return json.dumps(results, indent = 3)

#print(asyncio.run(get_items_around('-33.8670522,+151.1957362', 50, 2)))

async def eval_input(input):
    # Check which type of input it is
    option = check_input(input)
    # If none of the options work, return this
    error = '? %s' % input
    # If not valid return error
    if option == -1:
        return error
    
    message = input.split()

    # IAMAT option
    if option == 1:
        # Add client and info to dictionary
        clients[message[1]] = message[2:] + [sys.argv[1]]
        # Find time difference
        time_difference = str(float(current_time()) - float(message[3]))
        # Add plus sign if greater than zero
        if float(time_difference) > 0:
            time_difference = '+' + time_difference

        output = 'AT %s %s %s\n' % (sys.argv[1], time_difference, ' '.join(message[1:]))
        asyncio.ensure_future(flood_fill('CHANGE %s' % input, sys.argv[1]))
        return output
    
    # WHATSAT option
    if option == 2:
        # Check if the client is in the array
        if message[1] not in clients:
            return error
        client = clients[message[1]]
        location = get_coord(client[0])
        # Convert kilometres to metres
        radius = float(message[2]) * 1000
        items = int(message[3])

        # Find time difference
        time_difference = str(float(current_time()) - float(message[3]))
        # Add plus sign if greater than zero
        if float(time_difference) > 0:
            time_difference = '+' + time_difference

        output = 'AT %s %s %s %s %s' % (client[2], time_difference, message[1], client[0], client[1])
        locations = await get_items_around(location, radius, items)
        return output + '\n' + locations + '\n\n'
    return error

#print(asyncio.run(eval_input('IAMAT name -33.8670522+151.1957362 +33337')))
#print(asyncio.run(eval_input('WHATSAT name 10 1')))

# Flood fill to send change to servers
async def flood_fill(ins,server):
    # Send to each server it is connected to
    for s in send_to[server]:
        # See if you can sent message to server
        try:
            reader, writer = await asyncio.open_connection(IP_ADDR, ports[s])
            writer.write(ins.encode())
            await writer.drain()
            writer.close()
        # If can't (possibly because server is shut down), don't do anything
        except:
            #print('could not send')
            pass

async def handle_connection(reader, writer):
    data = await reader.readline()
    received = data.decode()
    time = current_time()

    message = received.split()
    # Check if first word is CHANGE with IAMAT formatted message after
    # CHANGE IAMAT client new_location time_sent
    if message[0] == 'CHANGE' and check_input(' '.join(message[1:])) == 1:
        if message[2] not in clients:
            clients[message[2]] = message[3:] + [sys.argv[1]]
            asyncio.ensure_future(flood_fill(received, sys.argv[1]))
            #print('added')
            #print(clients)
        else:
            # If the time of the new message is greater than the old time, change
            # If it has been updated it shouldn't update again
            if message[4] > clients[message[2]][2]:
                clients[message[2]] = message[3:] + [sys.argv[1]]
                asyncio.ensure_future(flood_fill(received, sys.argv[1]))
                #print('added')
                #print(clients)

    else:
        output = await eval_input(received)
        writer.write(output.encode())
        await writer.drain()
        writer.close()

async def main():
    """
    # Define servers
    Goloman = await asyncio.start_server(handle_connection, host = IP_ADDR, port = ports['Goloman'])
    Hands = await asyncio.start_server(handle_connection, host = IP_ADDR, port = ports['Hands'])
    Holiday = await asyncio.start_server(handle_connection, host = IP_ADDR, port = ports['Holiday'])
    Welsh = await asyncio.start_server(handle_connection, host = IP_ADDR, port = ports['Welsh'])
    Wilkes = await asyncio.start_server(handle_connection, host = IP_ADDR, port = ports['Wilkes'])

    # Initialize servers
    async with Goloman, Hands, Holiday, Welsh, Wilkes:
        await asyncio.gather(
            Goloman.serve_forever(),
            Hands.serve_forever(),
            Holiday.serve_forever(),
            Welsh.serve_forever(),
            Wilkes.serve_forever())
    """
    # Make sure there is server name after calling server
    if len(sys.argv) != 2:
        print("There has to be 2 arguments")
        sys.exit(1)

    # Check that the server name is one of the given server names
    if sys.argv[1] not in ports:
        print("Server name not one of possible servers")
        sys.exit(1)

    # Create server
    server = await asyncio.start_server(handle_connection, host = IP_ADDR, port = ports[sys.argv[1]])
    print(sys.argv[1])
    await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())