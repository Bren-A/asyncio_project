#!/usr/bin/env python3

import asyncio

IP_ADDR = '127.0.0.1'

ports = {
    'Goloman':11465, 
    'Hands':11466, 
    'Holiday':11467, 
    'Welsh':11468, 
    'Wilkes':11469
}

async def main():
    reader, writer = await asyncio.open_connection(IP_ADDR, 11465)
    print ('Sending...')
    writer.write(('IAMAT B -15-15 155555555.0').encode())
    
    data = await reader.readline()
    print(data.decode())

    writer.close()

if __name__ == '__main__':
    asyncio.run(main())    

"""
name = input("Name?\n")
connection = input("Which server to connect to?\n (Goloman/Hands/Holiday/Welsh/Wilkes)\n")

reader, writer = await asyncio.open_connection(IP_ADDR, ports[connection])

make_query = input("Connected. \n\nEnter query: \n(IAMAT/WHATSAT)\n")
if make_query == 'IAMAT':
    location = input("Location:\n(+/-Long+/-Lat)\n")
    time = current_time()

if make_query == 'WHATSAT':
    location = input("Distance from location:\n(In km 0 < x < 50)\n")
    time = input("How many results?\n(0 < x <= 20)")
query = '%s %s %s %s' % (make_query, name, location, time)

writer.write(query.encode())
data = await reader.readline()
print(data.decode())
writer.close()
"""