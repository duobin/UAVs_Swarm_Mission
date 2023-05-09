# This file defines all functions that is needed in both formation_main_leader.py and formation_main_follower.py

import time
import math
import Queue
import numpy as np
import dronekit
from dronekit import connect
from dronekit import VehicleMode
from dronekit import LocationGlobalRelative
from dronekit import mavutil
import geopy
from geopy.distance import vincenty
import socket
import threading
import multiprocessing
import os
# __builtin.variables can cross multiple files (for imported functions).
import __builtin__


# Constant parameters.
factor_deg2rad = math.pi/180.0

# MAVLink Parameters to specify coordinate frame.
# 1) MAV_FRAME_LOCAL_NED:
# Positions are relative to the vehicle's home position in the North, East, Down (NED) frame. Use this to specify a position x metres north, y metres east and (-) z metres above the home position.
# Velocity directions are in the North, East, Down (NED) frame.

# 2) MAV_FRAME_LOCAL_OFFSET_NED:
# Positions are relative to the current vehicle position in the North, East, Down (NED) frame. Use this to specify a position x metres north, y metres east and (-) z metres of the current vehicle position.
# Velocity directions are in the North, East, Down (NED) frame.

# 3) MAV_FRAME_BODY_OFFSET_NED:
# Positions are relative to the current vehicle position in a frame based on the vehicle's current heading. Use this to specify a position x metres forward from the current vehicle position, y metres to the right, and z metres down (forward, right and down are "positive" values).
# Velocity directions are relative to the current vehicle heading. Use this to specify the speed forward, right and down (or the opposite if you use negative values).

# 4) MAV_FRAME_BODY_NED:
# Positions are relative to the vehicle's home position in the North, East, Down (NED) frame. Use this to specify a position x metres north, y metres east and (-) z metres above the home position.
# Velocity directions are relative to the current vehicle heading. Use this to specify the speed forward, right and down (or the opposite if you use negative values).

# =============================================================


class FLAG_bool:
    global lock

    def __init__(self, bool_value=False):
        FLAG_bool.value = bool_value

    def set_true(self):
        with lock:
            FLAG_bool.value = True

    def set_false(self):
        with lock:
            FLAG_bool.value = False


class FLAG_control_word:
    global lock

    def __init__(self, control_word='P'):
        FLAG_control_word.value = control_word

    def set_run(self):
        with lock:
            FLAG_control_word.value = 'R'  # Run

    def set_pause(self):
        with lock:
            FLAG_control_word.value = 'P'  # Pause

    def set_terminate(self):
        with lock:
            FLAG_control_word.value = 'T'  # Terminate

# =============================================================

# TO START IT:
# threading.Thread(target=execute_function_in_queue, args=(queue,)).start()
# print(' Thread thread_send_gps has started!')


def execute_function_in_queue(queue):
    print('{} - execute_function_in_queue() is started.'.format(time.ctime()))
    # while not queue.empty():
    while True:
        func_and_args = queue.get()  # .get() will block when queue is empty.
        func = func_and_args[0]  # Get function name.
        if func == 'End':
            print(
                '{} - execute_function_in_queue() is terminated.\n'.format(time.ctime()))
            return
        else:
            args = func_and_args[1:]  # Get function arguments.
            func(*args)  # Execute function.

# =============================================================

# Check connections to router.


def CHECK_network_connection(vehicle, router_host, wait_time=None):
    print('{} - CHECK_network_connection({}) is started.'.format(time.ctime(), router_host))
    if wait_time == None:
        wait_time = 10  # Default wait time is 10 seconds.
    down_counter = 0
    while True:
        response = os.system('ping -c 1 ' + router_host)
        if response == 0:  # Link is OK.
            print(
                '{} - Connection to router is OK. Check again in {} seconds'.format(time.ctime(), wait_time))
            down_counter = 0  # Once connection is OK, reset counter.
            time.sleep(wait_time)  # Check again in wait_time seconds.
            continue  # Return back to the beginning of the while loop.
        else:  # Link is down.
            down_counter += 1
            print(
                '{} - Connection to router is DOWN for {} times.'.format(time.ctime(), down_counter))
            if down_counter > 5:
                print('{} - Reached maximum down times.'.format(time.ctime()))
                print('{} - Vehicle is returning home...'.format(time.ctime()))
                vehicle.mode = VehicleMode('RTL')
                break  # Terminate while loop.
            else:  # Have not reached max down times.
                print('{} - Check again in 1 seconds'.format(time.ctime()))
                time.sleep(1)  # Check again in 2 seconds.


# =============================================================
'''
(old)
# This function start server services.
# Be sure define the ports as global variables before call this function.
def start_SERVER_service(vehicle, is_leader, local_host):
    # 1) Start send gps coordinate service.
    threading.Thread(target=SERVER_send_gps_coordinate, args=(vehicle, local_host,)).start()
    print('{} - Thread SERVER_send_gps_coordinate is started!'.format(time.ctime()))
    # 2) Start send heading direction service.
    threading.Thread(target=SERVER_send_heading_direction, args=(vehicle, local_host,)).start()
    print('{} - Thread SERVER_send_heading_direction is started!'.format(time.ctime()))
    # 3) Start send follower status command.
    #    Be sure you have decleared a global variable __builtin__.status_waitForCommand.
    threading.Thread(target=SERVER_send_status, args=(local_host,)).start()
    print('{} - Thread SERVER_send_status has started!'.format(time.ctime()))
    # Leader drone does not need the following service.
    if not is_leader:
        # 4) Start SERVER_receive_and_execute_immediate_command service.
        # Be sure you have decleared a global variable __builtin__.status_waitForCommand.
        threading.Thread(target=SERVER_receive_and_execute_immediate_command, args=(local_host,)).start()
        print('{} - Thread SERVER_receive_and_execute_leader_immediate_command has been started!'.format(time.ctime()))
'''
# =============================================================

# This function start server services.
# Be sure define the ports as global variables before call this function.


def start_SERVER_service(vehicle, local_host):
    # 1) Start send gps coordinate service.
    threading.Thread(target=SERVER_send_gps_coordinate,
                     args=(vehicle, local_host,)).start()
    print('{} - Thread SERVER_send_gps_coordinate is started!'.format(time.ctime()))
    # 2) Start send heading direction service.
    threading.Thread(target=SERVER_send_heading_direction,
                     args=(vehicle, local_host,)).start()
    print('{} - Thread SERVER_send_heading_direction is started!'.format(time.ctime()))
    # 3) Start send follower status command.
    #    Be sure you have decleared a global variable __builtin__.status_waitForCommand.
    threading.Thread(target=SERVER_send_status, args=(local_host,)).start()
    print('{} - Thread SERVER_send_status has started!'.format(time.ctime()))

# =============================================================

# This is a server to send gps message.
# TO START IT:
# threading.Thread(target=SERVER_send_gps_coordinate, args=(local_host,)).start()
# print(' Thread thread_send_gps has started!')


def SERVER_send_gps_coordinate(vehicle, local_host):

    # Create a socket object
    msg_socket = socket.socket()
    msg_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind to the port
    msg_socket.bind((local_host, __builtin__.port_gps))
    msg_socket.listen(5)                 # Now wait for client connection.
    print('{} - SERVER_send_gps_coordinate() is started!'.format(time.ctime()))
    while True:
        # msg_socket.accept() will block while loop until the connection with client is established.
        # Establish connection with client.
        client_connection, client_address = msg_socket.accept()
        print('{} - Received GPS coordinate request from {}.'.format(time.ctime(), client_address))
        # Send message to client.
        # Get current GPS coordinate, compare with destination GPS coordinate.

        current_gps_coordinate = vehicle.location.global_relative_frame
        current_lat = current_gps_coordinate.lat
        current_lon = current_gps_coordinate.lon
        current_alt = current_gps_coordinate.alt

        current_lat_str = '{:.7f}'.format(current_lat)
        current_lon_str = '{:.7f}'.format(current_lon)
        current_alt_str = '{:.7f}'.format(current_alt)
        gps_msg_str = current_lat_str + ',' + current_lon_str + ',' + current_alt_str
        client_connection.send(gps_msg_str)
        # Socket is destroyed when message has been sent.
        client_connection.close()

# =============================================================

# This is a server to send vehicle heading direction information.
# TO START IT:
# threading.Thread(target=SERVER_send_heading_direction, args=(local_host,)).start()
# print(' Thread SERVER_send_heading_direction() has started!')


def SERVER_send_heading_direction(vehicle, local_host):
    # Create a socket object
    msg_socket = socket.socket()
    msg_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind to the port
    msg_socket.bind((local_host, __builtin__.port_heading))
    msg_socket.listen(5)
    print('{} - SERVER_send_heading_direction() is started!'.format(time.ctime()))
    while True:
        # msg_socket.accept() will block while loop until the connection with client is established.
        # Establish connection with client.
        client_connection, client_address = msg_socket.accept()
        print('{} - Received heading direction request from {}.'.format(time.ctime(), client_address))
        # Send message to client.
        # Get current heading.
        heading = vehicle.heading
        current_heading_str = str(heading)
        client_connection.send(current_heading_str)
        # Socket is destroyed when message has been sent.
        client_connection.close()

# =============================================================
# Caution: This function has to be copied to the main file. Because exec('command', globals()) can only access the variable within the same script.
# This is a server to receive leader drone's command message.
# CAUTION: This function will execute commands from any host. Check mechanism can be added.
# TO START IT:
# threading.Thread(target=SERVER_receive_and_execute_immediate_command, args=(local_host,)).start()


def SERVER_receive_and_execute_immediate_command(local_host):
    # Create a socket object
    msg_socket = socket.socket()
    msg_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind to the port
    msg_socket.bind((local_host, __builtin__.port_immediate_command))
    msg_socket.listen(5)                 # Now wait for client connection.
    print('{} - SERVER_receive_and_execute_immediate_command() is started!'.format(time.ctime()))
    while True:
        # msg_socket.accept() will block while loop until the connection with client is established.
        # Establish connection with client.
        client_connection, client_address = msg_socket.accept()
        print('\n{} - Received immediate command from {}.'.format(time.ctime(), client_address))
        # Receive message.
        immediate_command_str = client_connection.recv(1024)
        print('{} - Immediate command is: {}'.format(time.ctime(), immediate_command_str))
        # If command is 'break', execute immediately, regardless of the status of follower drone.
        if immediate_command_str == 'air_break()':
            # Execute received command.
            exec(immediate_command_str, globals())
            # When command is executed, change status to 'wait for command'.
            __builtin__.status_waitForCommand = True
            print('{} - Immediate command \'{}\' is finished!'.format(time.ctime(),
                  immediate_command_str))
        # If command is not 'Break', and __builtin__.status_waitForCommand is true, execute command immediately.
        else:  # immediate_command_str is not 'air_break()'
            if __builtin__.status_waitForCommand == True:
                # Change __builtin__.status_waitForCommand to False to block other calls.
                __builtin__.status_waitForCommand = False
                # Execute immediate command.
                exec(immediate_command_str, globals())
                # Change __builtin__.status_waitForCommand to True to enable other calls.
                __builtin__.status_waitForCommand = True
                print(
                    '{} - Immediate command \'{}\' is finished!'.format(time.ctime(), immediate_command_str))
            else:  # __builtin__.status_waitForCommand == False:
                print('{} - Omit immediate command \'{}\', because __builtin__.status_waitForCommand is False!'.format(
                    time.ctime(), immediate_command_str))
        # Socket is destroyed when message has been sent.
        client_connection.close()

# =============================================================

# This is a server to send __builtin__.status_waitForCommand to requester.
# TO START IT:
# Declare a global variable __builtin__.status_waitForCommand in main function.
# threading.Thread(target=SERVER_send_status, args=(local_host,)).start()
# print(' Thread SERVER_send_status has started!')


def SERVER_send_status(local_host):
    # Create a socket object
    msg_socket = socket.socket()
    msg_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind to the port
    msg_socket.bind((local_host, __builtin__.port_status))
    msg_socket.listen(5)                 # Now wait for client connection.
    print('{} - SERVER_send_status() is started!'.format(time.ctime()))
    while True:
        # msg_socket.accept() will block while loop until the connection with client is established.
        # Establish connection with client.
        client_connection, client_address = msg_socket.accept()
        print('{} - Received follower status request from {}.'.format(time.ctime(), client_address))
        # Send message to client.
        client_connection.send(str(int(__builtin__.status_waitForCommand)))
        # Socket is destroyed when message has been sent.
        client_connection.close()

# =============================================================

# This is a client to send immediate command to remote host.


def CLIENT_send_immediate_command(remote_host, immediate_command_str):
    # Create a socket object
    client_socket = socket.socket()
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        client_socket.connect(
            (remote_host, __builtin__.port_immediate_command))
    except socket.error as error_msg:
        print('{} - Caught exception : {}'.format(time.ctime(), error_msg))
        print('{} - CLIENT_send_immediate_command({}, {}) is not executed!'.format(
            time.ctime(), remote_host, immediate_command_str))
        return
    client_socket.send(immediate_command_str)

# =============================================================

# This is a client to request remote host's status.


def CLIENT_request_status(remote_host):
    # Create a socket object
    client_socket = socket.socket()
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        client_socket.connect((remote_host, __builtin__.port_status))
    except socket.error as error_msg:
        print('{} - Caught exception : {}'.format(time.ctime(), error_msg))
        print('{} - CLIENT_request_status({}) is not executed!'.format(time.ctime(), remote_host))
        return False
    status_msg_str = client_socket.recv(1024)
    return bool(int(status_msg_str))

# =============================================================

# This is a client to receive remote host's gps coordinate.


def CLIENT_request_gps(remote_host):

    # Create a socket object
    client_socket = socket.socket()
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        client_socket.connect((remote_host, __builtin__.port_gps))
    except socket.error as error_msg:
        print('{} - Caught exception : {}'.format(time.ctime(), error_msg))
        print(
            '{} - CLIENT_request_gps({}) is not executed!'.format(time.ctime(), remote_host))
        return None, None, None
    gps_msg_str = client_socket.recv(1024)
    # Return lat, lon, and alt
    lat, lon, alt = gps_msg_str.split(',')
    return float(lat), float(lon), float(alt)

# =============================================================

# This is a client to receive remote host's heading direction.


def CLIENT_request_heading_direction(remote_host):
    # Create a socket object
    client_socket = socket.socket()
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        client_socket.connect((remote_host, __builtin__.port_heading))
    except socket.error as error_msg:
        print('{} - Caught exception : {}'.format(time.ctime(), error_msg))
        print('{} - CLIENT_request_heading_direction({}) is not executed!'.format(time.ctime(), remote_host))
        return None
    heading_msg_str = client_socket.recv(1024)
    return int(heading_msg_str)

# =============================================================

# This function should run on leader drone.


def wait_for_follower_ready(follower_host_tuple):
    all_follower_status = []
    for follower_host in follower_host_tuple:
        iter_follower_status = CLIENT_request_status(follower_host)
        all_follower_status.append(iter_follower_status)
    while not all(all_follower_status):  # If there is anyone who is False.
        for i in range(len(follower_host_tuple)):
            if not all_follower_status[i]:
                print('{} - Host {} is not ready.'.format(time.ctime(),
                      follower_host_tuple[i]))
        print('{} - Wait for 1 second.'.format(time.ctime()))
        time.sleep(1)
        # Reset status.
        all_follower_status = []
        # Check all followers' status again.
        for follower_host in follower_host_tuple:
            iter_follower_status = CLIENT_request_status(follower_host)
            all_follower_status.append(iter_follower_status)

# =============================================================

# The function send_ned_velocity() below generates a SET_POSITION_TARGET_LOCAL_NED MAVLink message. It directly specify the speed components of the vehicle in the MAV_FRAME_LOCAL_NED frame.
# Velocity is relative to the vehicle's home position.
# Velocity directions are in the North, East, Down (NED) frame.
# The message is re-sent every second for the specified duration.


def send_local_ned_velocity(vehicle, velocity_x, velocity_y, velocity_z, duration):
    """
    Move vehicle in direction based on specified velocity vectors.
    """
    print('\n')
    print('{} - Calling function send_local_ned_velocity(Vx={}, Vy={}, Vz={}, Duration={})'.format(
        time.ctime(), velocity_x, velocity_y, velocity_z, duration))
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,  # frame
        0b0000111111000111,  # type_mask (only speeds enabled)
        0, 0, 0,  # x, y, z positions (not used)
        velocity_x, velocity_y, velocity_z,  # x, y, z velocity in m/s
        # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0, 0,
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    # send command to vehicle on 1 Hz cycle
    for x in range(0, int(math.ceil(duration))):
        vehicle.send_mavlink(msg)
        print('{} - Local NED Velocity command is sent! Vx={}, Vy={}, Vz={}'.format(
            time.ctime(), velocity_x, velocity_y, velocity_z))
        print('{} - Duration = {} seconds'.format(time.ctime(), x+1))
        time.sleep(1)
        get_vehicle_state(vehicle)
        print('\n')

# ===================================================

# The function send_body_frame_velocity() below generates a SET_POSITION_TARGET_LOCAL_NED MAVLink message. It directly specify the speed components of the vehicle in the MAV_FRAME_BODY_OFFSET_NED frame.
# Vx: forward from the current vehicle position, Vy: to the right, Vz: down (forward, right and down are "positive" values).
# Velocity is relative to the current vehicle heading.
# Use this to specify the speed forward, right and down (or the opposite if you use negative values).
# The message is re-sent every second for the specified duration.


def send_body_frame_velocity(vehicle, velocity_x, velocity_y, velocity_z, duration):
    """
    Move vehicle in direction based on specified velocity vectors.
    """
    print('\n')
    print('{} - Calling function send_body_frame_velocity(Vx={}, Vy={}, Vz={}, Duration={})'.format(
        time.ctime(), velocity_x, velocity_y, velocity_z, duration))
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED,  # frame
        0b0000111111000111,  # type_mask (only speeds enabled)
        0, 0, 0,  # x, y, z positions (not used)
        velocity_x, velocity_y, velocity_z,  # x, y, z velocity in m/s
        # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0, 0,
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    # send command to vehicle on 1 Hz cycle
    for x in range(0, int(math.ceil(duration))):
        vehicle.send_mavlink(msg)
        print('{} - Body Frame Velocity command is sent! Vx={}, Vy={}, Vz={}'.format(
            time.ctime(), velocity_x, velocity_y, velocity_z))
        print('{} - Duration = {} seconds'.format(time.ctime(), x+1))
        time.sleep(1)
        get_vehicle_state(vehicle)
        print('\n')

# ===================================================


# The function send_body_frame_velocity() below generates a SET_POSITION_TARGET_LOCAL_NED MAVLink message. It directly specify the speed components of the vehicle in the MAV_FRAME_BODY_OFFSET_NED frame.
# Vx: forward from the current vehicle position, Vy: to the right, Vz: down (forward, right and down are "positive" values).
# Velocity is relative to the current vehicle heading.
# Use this to specify the speed forward, right and down (or the opposite if you use negative values).
# The message is send only once.
def send_body_frame_velocity_once(vehicle, velocity_x, velocity_y, velocity_z):
    """
    Move vehicle in direction based on specified velocity vectors.
    """
    print('\n')
    print('{} - Calling function send_body_frame_velocity(Vx={}, Vy={}, Vz={})'.format(
        time.ctime(), velocity_x, velocity_y, velocity_z))
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED,  # frame
        0b0000111111000111,  # type_mask (only speeds enabled)
        0, 0, 0,  # x, y, z positions (not used)
        velocity_x, velocity_y, velocity_z,  # x, y, z velocity in m/s
        # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0, 0,
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    # send command to vehicle
    vehicle.send_mavlink(msg)
    print('{} - Body Frame Velocity command is sent! Vx={}, Vy={}, Vz={}'.format(
        time.ctime(), velocity_x, velocity_y, velocity_z))
    get_vehicle_state(vehicle)
    print('\n')

# ===================================================


def send_body_frame_yaw_once(vehicle, turn_degree, turn_direction):
    # create the CONDITION_YAW command using command_long_encode()
    # turn_direction  1 : clockwise (From top look down)
    # turn_direction -1 : counter clockwise (From top look down)
    msg_yaw = vehicle.message_factory.command_long_encode(
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW,  # command
        0,  # confirmation
        turn_degree,  # param 1, yaw in degrees
        0,          # param 2, yaw speed deg/s
        turn_direction,  # param 3, direction -1 ccw(subtract), 1 cw(add)
        # param 4, if set to 0, yaw is an absolute direction[0-360](0=north, 90=east); if set to 1, yaw is a relative degree to the current yaw direction.
        1,
        0, 0, 0)    # param 5 ~ 7 not used
    vehicle.send_mavlink(msg_yaw)

# ===================================================


def curvature_flight_body_frame(vehicle, horizontal_linear_speed, radius_of_curvature, total_turn_degree_deg, velocity_z, atom_segment):
    print('\n')
    print('{} - Calling function curvature_flight_body_frame(horizontal_linear_speed={}, radius_of_curvature={}, total_turn_degree_deg={}, velocity_z={})'.format(
        time.ctime(), horizontal_linear_speed, radius_of_curvature, total_turn_degree_deg, velocity_z))
    # Get sign of radius_of_curvature. # Positive: turn right. Negative: turn left.
    turn_direction = np.sign(radius_of_curvature)
    # Convert int to float.
    # Only keep magnitude.
    horizontal_linear_speed = float(abs(horizontal_linear_speed))
    # Only keep magnitude.
    radius_of_curvature = float(abs(radius_of_curvature))
    # Only keep magnitude.
    total_turn_degree_deg = float(abs(total_turn_degree_deg))
    atom_segment = float(abs(atom_segment))
    # Calculate angular velocity. Angular velocity = horizontal_linear_speed/radius_of_curvature
    angular_velocity = horizontal_linear_speed/radius_of_curvature
    # Split circle into fine polygon.
    atom_angle_rad = atom_segment / radius_of_curvature
    atom_angle_deg = atom_angle_rad / factor_deg2rad  # Convert deg to rad.
    # Time interval between sending two consecutive speed specify command.
    delta_t = atom_angle_rad/angular_velocity
    # Calculate Vx and Vy.
    # velocity_x = turn_direction * horizontal_linear_speed * math.sin(atom_angle_rad)
    # velocity_y = horizontal_linear_speed * math.cos(atom_angle_rad)
    # Construct MAVlink message.
    msg_velocity = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED,  # frame
        0b0000111111000111,  # type_mask (only speeds enabled)
        0, 0, 0,  # x, y, z positions (not used)
        # x, y, z velocity in m/s. x direction is forward.
        horizontal_linear_speed, 0, velocity_z,
        # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0, 0,
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    # create the CONDITION_YAW command using command_long_encode()
    msg_yaw = vehicle.message_factory.command_long_encode(
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW,  # command
        0,  # confirmation
        atom_angle_deg,  # param 1, yaw in degrees
        0,          # param 2, yaw speed deg/s
        turn_direction,  # param 3, direction -1 ccw(subtract), 1 cw(add)
        # param 4, if set to 0, yaw is an absolute direction[0-360](0=north, 90=east); if set to 1, yaw is a relative degree to the current yaw direction.
        1,
        0, 0, 0)    # param 5 ~ 7 not used

    # After taking off, yaw commands are ignored until the first "movement" command has been received. If you need to yaw immediately following takeoff then send a command to "move" to your current position. Make sure send a dummy_movement() before send yaw.
    # Send command to vehicle every delta_t seconds.
    time_temp = time.ctime()
    print('{} - horizontal_linear_speed={} m/s.'.format(time_temp,
          horizontal_linear_speed))
    print('{} - radius_of_curvature={} m.'.format(time_temp,
          turn_direction * radius_of_curvature))
    print('{} - atom_segment={} m.'.format(time_temp, atom_segment))
    print('{} - atom_angle_deg={} degree.'.format(time_temp, atom_angle_deg))
    print('{} - delta_t={} s.'.format(time_temp, delta_t))
    print('{} - angular_velocity={} rad/s.'.format(time_temp, angular_velocity))
    print('\n')

    remaining_degree_to_turn = total_turn_degree_deg
    while (remaining_degree_to_turn > 0):
        # if remaining_degree_to_turn < atom_angle_deg, generate new msg_yaw.
        if (remaining_degree_to_turn < atom_angle_deg):
            # create the CONDITION_YAW command using command_long_encode()
            msg_yaw = vehicle.message_factory.command_long_encode(
                0, 0,    # target system, target component
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,  # command
                0,  # confirmation
                remaining_degree_to_turn,  # param 1, yaw in degrees
                0,          # param 2, yaw speed deg/s
                # param 3, direction -1 ccw(subtract), 1 cw(add)
                turn_direction,
                # param 4, if set to 0, yaw is an absolute direction[0-360](0=north, 90=east); if set to 1, yaw is a relative degree to the current yaw direction.
                1,
                0, 0, 0)    # param 5 ~ 7 not used
            # Use shorter delta_t
            delta_t = delta_t * remaining_degree_to_turn / atom_angle_deg

        print('{} - Remaining degree to turn = {} degrees'.format(time.ctime(),
              remaining_degree_to_turn))
        print('{} - Sending mavlink message msg_yaw, atom_angle_deg={}, turn_direction={}.'.format(
            time.ctime(), atom_angle_deg, turn_direction))
        vehicle.send_mavlink(msg_yaw)
        print('{} - Sending mavlink message msg_velocity, horizontal_linear_speed={}.'.format(
            time.ctime(), horizontal_linear_speed))
        vehicle.send_mavlink(msg_velocity)
        time.sleep(delta_t)
        remaining_degree_to_turn -= atom_angle_deg
        get_vehicle_state(vehicle)
        print('\n')

# ===================================================

# The function send_local_ned_position() below generates a SET_POSITION_TARGET_LOCAL_NED MAVLink message. It directly specify the position components of the vehicle in the MAV_FRAME_LOCAL_NED frame.
# Position is relative to the vehicle's home position (launch location).
# Position directions are in the North, East, Down (NED) frame.
# The function will wait for an estimated time to finish the moving.


def move_inLocalFrame(vehicle, north, east, down, groundspeed):
    print('\n')
    print('{} - Calling function move_inLocalFrame(North={}, East={}, Down={}, groundspeed={})'.format(
        time.ctime(), north, east, down, groundspeed))
    # Time estimation.
    estimatedGroundDistance = math.sqrt(north**2 + east**2)
    if groundspeed > 0:
        estimatedHorizontalFlightTime = estimatedGroundDistance / groundspeed
    else:
        estimatedHorizontalFlightTime = 1
    if not down:  # if down is zero
        # We only need to consider the time needed for level flight.
        estimatedTime = estimatedHorizontalFlightTime
        print('{} - 2-Dimension Horizontal flight, estimatied flight time is : {}'.format(
            time.ctime(), estimatedTime))
    else:  # if down is not zero
        estimatedTime = estimatedHorizontalFlightTime + 5
        print('{} - 3-Dimension fight, estimatied flight time is : {}'.format(time.ctime(), estimatedTime))

    # Generate MAVLink message.
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,  # frame
        0b0000111111111000,  # type_mask (only position enabled)
        north, east, down,  # north, east, down positions in meters.
        0, 0, 0,  # x, y, z velocity (not used)
        # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0, 0,
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    # Set ground speed.
    vehicle.groundspeed = groundspeed
    print('{} - Groundspeed is set to {} m/s.'.format(time.ctime(), vehicle.groundspeed))

    # Send MAVLink message.
    vehicle.send_mavlink(msg)

    # Wait estimated time for command to be fully executed.
    for t in range(0, int(math.ceil(estimatedTime))):
        time.sleep(1)
        print('{} - Executed move_inLocalFrame(North={}, East={}, Down={}, groundspeed={}) for {} seconds.'.format(
            time.ctime(), north, east, down, groundspeed, t+1))
        get_vehicle_state(vehicle)
        print('\n')

# ===================================================

# The function move_inBodyFrame() below generates a SET_POSITION_TARGET_LOCAL_NED MAVLink message. It directly specify the position components of the vehicle in the MAV_FRAME_LOCAL_NED frame.
# Position is relative to the vehicle's current position.
# Position forward, right and down are "positive" values.
# IMPORTANT: Drone will turn its head toward to travel direction.
# The function will wait for an estimated time to finish the moving.


def move_inBodyFrame(vehicle, forward, right, down, groundspeed):
    print('\n')
    print('{} - Calling function move_inBodyFrame(forward={}, right={}, down={}, groundspeed={})'.format(
        time.ctime(), forward, right, down, groundspeed))
    # Time estimation.
    estimatedGroundDistance = math.sqrt(forward**2 + right**2)
    if groundspeed > 0:
        estimatedHorizontalFlightTime = estimatedGroundDistance / groundspeed
    else:
        estimatedHorizontalFlightTime = 1
    if not down:  # if down is zero
        # We only need to consider the time needed for level flight.
        estimatedTime = estimatedHorizontalFlightTime
        print('{} - 2-Dimension Horizontal flight, estimatied flight time is : {}'.format(
            time.ctime(), estimatedTime))
    else:  # if down is not zero
        estimatedTime = estimatedHorizontalFlightTime + 5
        print('{} - 3-Dimension fight, estimatied flight time is : {}'.format(time.ctime(), estimatedTime))

    # Generate MAVLink message.
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED,  # frame
        0b0000111111111000,  # type_mask (only position enabled)
        forward, right, down,  # positions in meters.
        0, 0, 0,  # x, y, z velocity (not used)
        # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0, 0,
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    # Set ground speed.
    vehicle.groundspeed = groundspeed
    print('{} - Groundspeed is set to {} m/s.'.format(time.ctime(), vehicle.groundspeed))

    # Send MAVLink message.
    vehicle.send_mavlink(msg)

    # Wait estimated time for command to be fully executed.
    for t in range(0, int(math.ceil(estimatedTime))):
        time.sleep(1)
        print('{} - Executed move_inBodyFrame(forward={}, right={}, down={}, groundspeed={}) for {} seconds.'.format(
            time.ctime(), forward, right, down, groundspeed, t+1))
        get_vehicle_state(vehicle)
        print('\n')

# ===================================================

# Go to specified GPS coordinate.
# lat: Latitude.
# lon: Longitude.
# alt: Altitude in meters(relative to the home location).


def goto_gps_location_relative(vehicle, lat, lon, alt, groundspeed=None):
    print('\n')
    print('{} - Calling goto_gps_location_relative(lat={}, lon={}, alt={}, groundspeed={}).'.format(
        time.ctime(), lat, lon, alt, groundspeed))
    destination = LocationGlobalRelative(lat, lon, alt)
    print('{} - Before calling goto_gps_location_relative(), vehicle state is:'.format(time.ctime()))
    get_vehicle_state(vehicle)
    # Get current GPS coordinate, compare with destination GPS coordinate.
    current_lat = vehicle.location.global_relative_frame.lat
    current_lon = vehicle.location.global_relative_frame.lon
    current_alt = vehicle.location.global_relative_frame.alt
    # Wait until reach destination.
    while ((distance_between_two_gps_coord((current_lat, current_lon), (lat, lon)) > 0.5) or (abs(current_alt-alt) > 0.3)):
        # Execute fly command.
        vehicle.simple_goto(destination, groundspeed=groundspeed)
        # wait for one second.
        time.sleep(0.5)
        # Check current GPS coordinate, compare with destination GPS coordinate.
        current_lat = vehicle.location.global_relative_frame.lat
        current_lon = vehicle.location.global_relative_frame.lon
        current_alt = vehicle.location.global_relative_frame.alt
        print('{} - Horizontal distance to destination: {} m.'.format(time.ctime(),
              distance_between_two_gps_coord((current_lat, current_lon), (lat, lon))))
        print('{} - Perpendicular distance to destination: {} m.'.format(time.ctime(), current_alt-alt))
    # When finishe, check vehicle status.
    print('{} - After calling goto_gps_location_relative(), vehicle state is:'.format(time.ctime()))
    get_vehicle_state(vehicle)

# ===================================================

# Go to specified GPS coordinate on leaders command.
# lat: Latitude.
# lon: Longitude.
# alt: Altitude in meters(relative to the home location).


def goto_gps_location_relative(vehicle, lat, lon, alt, groundspeed=None):
    print('\n')
    print('{} - Calling goto_gps_location_relative(lat={}, lon={}, alt={}, groundspeed={}).'.format(
        time.ctime(), lat, lon, alt, groundspeed))
    destination = LocationGlobalRelative(lat, lon, alt)
    print('{} - Before calling goto_gps_location_relative(), vehicle state is:'.format(time.ctime()))
    get_vehicle_state(vehicle)
    # Get current GPS coordinate, compare with destination GPS coordinate.
    current_lat = vehicle.location.global_relative_frame.lat
    current_lon = vehicle.location.global_relative_frame.lon
    current_alt = vehicle.location.global_relative_frame.alt

    while ((distance_between_two_gps_coord((current_lat, current_lon), (lat, lon)) > 0.5) or (abs(current_alt-alt) > 0.3)):
        # Execute fly command.
        vehicle.simple_goto(destination, groundspeed=groundspeed)
        # wait for one second.
        time.sleep(0.5)
        # Check current GPS coordinate, compare with destination GPS coordinate.
        current_lat = vehicle.location.global_relative_frame.lat
        current_lon = vehicle.location.global_relative_frame.lon
        current_alt = vehicle.location.global_relative_frame.alt
        print('{} - Horizontal distance to destination: {} m.'.format(time.ctime(),
              distance_between_two_gps_coord((current_lat, current_lon), (lat, lon))))
        print('{} - Perpendicular distance to destination: {} m.'.format(time.ctime(), current_alt-alt))

    print('{} - After calling goto_gps_location_relative(), vehicle state is:'.format(time.ctime()))
    get_vehicle_state(vehicle)

# ===================================================

# The vehicle "yaw" is the direction that the vehicle is facing in the horizontal plane.
# On Copter this yaw need not be the direction of travel (though it is by default).
# The yaw will return to the default (facing direction of travel) after you set the mode or change the command used for controlling movement.
# At time of writing there is no safe way to return to the default yaw "face direction of travel" behaviour.
# After taking off, yaw commands are ignored until the first "movement" command has been received. If you need to yaw immediately following takeoff then send a command to "move" to your current position


def set_yaw(vehicle, yaw_inDegree, bool_isRelative):
    print('\n')
    print('{} - Calling function set_yaw(yaw_inDegree={}, bool_isRelative={}).'.format(
        time.ctime(), yaw_inDegree, bool_isRelative))
    # Do not pass True or False into msg, just in case the conversion is unpredictable.
    if bool_isRelative:
        is_relative = 1
        print(
            '{} - The degree to turn is relative to current heading.'.format(time.ctime()))
        degreeToTurn = yaw_inDegree
        if degreeToTurn > 180:
            degreeToTurn = 360 - degreeToTurn
        # Upon testing, the turning speed is 30 degree/second. Add one more second.
        estimatedTime = degreeToTurn/30.0 + 1
        print('{} - Absolute degree to turn is {} degree. Estimated time is {} seconds.'.format(
            time.ctime(), degreeToTurn, estimatedTime))
    else:
        is_relative = 0
        print(
            '{} - The target degree is absolute degree[0~360](0=North, 90=East).'.format(time.ctime()))
        currentHeading = vehicle.heading
        print('{} - Current heading is {} degree.'.format(time.ctime(), currentHeading))
        print('{} - Target heading is {} degree.'.format(time.ctime(), yaw_inDegree))
        degreeToTurn = abs(yaw_inDegree - vehicle.heading)
        if degreeToTurn > 180:
            degreeToTurn = 360 - degreeToTurn
        # Upon testing, the turning speed is 30 degree/second. Add one more second.
        estimatedTime = degreeToTurn/30.0 + 1
        print('{} - Absolute degree to turn is {} degree. Estimated time is {} seconds.'.format(
            time.ctime(), degreeToTurn, estimatedTime))

    # create the CONDITION_YAW command using command_long_encode()
    msg = vehicle.message_factory.command_long_encode(
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW,  # command
        0,  # confirmation
        yaw_inDegree,  # param 1, yaw in degrees
        0,          # param 2, yaw speed deg/s
        1,          # param 3, direction -1 ccw, 1 cw
        # param 4, if set to 0, yaw is an absolute direction[0-360](0=north, 90=east); if set to 1, yaw is a relative degree to the current yaw direction.
        is_relative,
        0, 0, 0)    # param 5 ~ 7 not used

    # Send MAVLink message.
    vehicle.send_mavlink(msg)

    # Wait sort of time for the command to be fully executed.
    for t in range(0, int(math.ceil(estimatedTime))):
        time.sleep(1)
        print('{} - Executed set_yaw(yaw_inDegree={}, bool_isRelative={}) for {} seconds.'.format(
            time.ctime(), yaw_inDegree, bool_isRelative, t+1))
        get_vehicle_state(vehicle)
        print('\n')

# ===================================================

# Calculate new gps coordinate given one point(lat, lon), direction(bearing), and distance. A bearing of 90 degrees corresponds to East, 180 degrees is South, and so on.


def new_gps_coord_after_offset_inLocalFrame(original_gps_coord, displacement, rotation_degree):
    vincentyDistance = geopy.distance.VincentyDistance(meters=displacement)
    original_point = geopy.Point(original_gps_coord[0], original_gps_coord[1])
    new_gps_coord = vincentyDistance.destination(
        point=original_point, bearing=rotation_degree)
    new_gps_lat = new_gps_coord.latitude
    new_gps_lon = new_gps_coord.longitude
    # If convert float to decimal, round will be accurate, but will take 50% more time. Not necessary.
    # new_gps_lat = decimal.Decimal(new_gps_lat)
    # new_gps_lon = decimal.Decimal(new_gps_lon)
    return (round(new_gps_lat, 7), round(new_gps_lon, 7))

# ===================================================

# Calculate new gps coordinate given one point(lat, lon), direction(bearing), and distance. A bearing of 90 degrees corresponds to East, 180 degrees is South, and so on.


def new_gps_coord_after_offset_inBodyFrame(original_gps_coord, displacement, current_heading, rotation_degree_relative):
    # current_heading is in degree, North = 0, East = 90.
    # Get rotation degree in local frame.
    rotation_degree_absolute = rotation_degree_relative + current_heading
    if rotation_degree_absolute >= 360:
        rotation_degree_absolute -= 360
    vincentyDistance = geopy.distance.VincentyDistance(meters=displacement)
    original_point = geopy.Point(original_gps_coord[0], original_gps_coord[1])
    new_gps_coord = vincentyDistance.destination(
        point=original_point, bearing=rotation_degree_absolute)
    new_gps_lat = new_gps_coord.latitude
    new_gps_lon = new_gps_coord.longitude
    # If convert float to decimal, round will be accurate, but will take 50% more time. Not necessary.
    # new_gps_lat = decimal.Decimal(new_gps_lat)
    # new_gps_lon = decimal.Decimal(new_gps_lon)
    return (round(new_gps_lat, 7), round(new_gps_lon, 7))

# ===================================================

# Calculate the distance between two gps coordinate. Return distance in meters.
# 2D.


def distance_between_two_gps_coord(point1, point2):
    distance = vincenty(point1, point2).meters
    return distance

# ===================================================


def preArm_override(vehicle):
    # vehicle.channels['1'] : Roll
    # vehicle.channels['2'] : Pitch
    # vehicle.channels['3'] : Throttle
    # vehicle.channels['4'] : Yaw
    # If arm without Radio Contoller(RC is turned off), the value of each channel will be 0.
    # The failsafe check requires the throttle value(vehicle.vhannels['3']) to be above failsafe value.
    # value(vehicle.parameters.get('FS_THR_VALUE')).
    # To bypass throttle failsafe check, you need to override channel 3.
    # The range of FS_THR_VALUE is (925 ~ 1100), so we can set channel 3 to 1100.
    vehicle.channels.overrides['3'] = 1100
    # Caution: Do not set channel 3 any higher value, or the vehicle will thrust when armed.

# ===================================================


def arm_no_RC(vehicle):
    # Override RC channel 3, which is the throttle channel.
    preArm_override(vehicle)
    time.sleep(3)

    # Wait for 3 seconds after overriding the throttle channel. Make sure the value is sent to pixhawk.
    # time.sleep(3)

    # Wait till the vehicle is armable.
    while not vehicle.is_armable:
        print('{} - Vehicle is not armable, waiting for vehicle to initialise...'.format(time.ctime()))
        preArm_override(vehicle)
        time.sleep(3)

    # When vehicle is armable, change mode to GUIDED and try to arm it.
    print('{} - Arming motors...'.format(time.ctime()))

    # Copter should arm in GUIDED mode
    vehicle.mode = VehicleMode('GUIDED')
    # Wait for 3 seconds after mode change. Make sure the value is sent.
    time.sleep(3)
    # Check if the vehicle mode is GUIDED.
    print('{} - Vehicle mode is changed to {}'.format(time.ctime(), vehicle.mode.name))

    # Try to arm vehicle. The first time will be probably failed. It will initialize APM. After initializing, the second time will be a succeed.
    vehicle.armed = True
    # If the first time arming failed, arm again till success.
    while not vehicle.armed:
        print('{} - Vehicle is not armed, try to arm vehicle again...'.format(time.ctime()))
        time.sleep(3)
        vehicle.armed = True

# ===================================================


def air_break(vehicle):
    if vehicle.armed:
        print('\n')
        print('{} - Calling function air_break().'.format(time.ctime()))

        msg = vehicle.message_factory.set_position_target_local_ned_encode(
            0,       # time_boot_ms (not used)
            0, 0,    # target system, target component
            mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED,  # frame
            0b0000111111000111,  # type_mask (only speeds enabled)
            0, 0, 0,  # x, y, z positions (not used)
            0, 0, 0,  # x, y, z velocity in m/s
            # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
            0, 0, 0,
            0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

        # Send message one time, then check the speed, if not stop, send again.
        print('{} - Sending air break command first time.'.format(time.ctime()))
        vehicle.send_mavlink(msg)
        get_vehicle_state(vehicle)
        while ((vehicle.velocity[0]**2+vehicle.velocity[1]**2+vehicle.velocity[2]**2) > 0.1):
            print('{} - Sending air break command once again.'.format(time.ctime()))
            vehicle.send_mavlink(msg)
            print('{} - Body Frame Velocity command is sent! Vx={}, Vy={}, Vz={}'.format(
                time.ctime(), vehicle.velocity[0], vehicle.velocity[1], vehicle.velocity[2]))
            time.sleep(1)
            get_vehicle_state(vehicle)
            print('\n')
    else:
        print('{} - Vehicle is not armed, no need to break.'.format(time.ctime()))

# ===================================================

# After taking off, yaw commands are ignored until the first "movement" command has been received. If you need to yaw immediately following takeoff then send a command to "move" to your current position.
# This dummy_movement is used to partially fix this buy.


def dummy_movement(vehicle):
    print('\n')
    print('{} - Calling function dummy_movement().'.format(time.ctime()))
    msg = vehicle.message_factory.set_position_target_global_int_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # frame
        0b0000111111000111,  # type_mask (only speeds enabled)
        0,  # lat_int - X Position in WGS84 frame in 1e7 * meters
        0,  # lon_int - Y Position in WGS84 frame in 1e7 * meters
        # alt - Altitude in meters in AMSL altitude(not WGS84 if absolute or relative)
        0,
        # altitude above terrain if GLOBAL_TERRAIN_ALT_INT
        0,  # X velocity in NED frame in m/s
        0,  # Y velocity in NED frame in m/s
        0,  # Z velocity in NED frame in m/s
        # afx, afy, afz acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0, 0,
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    # send command to vehicle on 2 times.
    vehicle.send_mavlink(msg)
    time.sleep(0.5)
    vehicle.send_mavlink(msg)
    time.sleep(0.5)

# ===================================================


'''
# This message has to be sent again and again.
def fly_follow_leader_onCommand(args_tuple_str):
    global leader_host
    
    # Block other commands.
    __builtin__.status_waitForCommand = False
    
    # Get parameters. All original parameters are in string type.
    frame = str(args_tuple_str[0].strip()) # Relative to leader's body frame, or to local frame.
    height = float(args_tuple_str[1].strip()) # Follower's altitude relative to home location.
    radius_2D = float(args_tuple_str[2].strip()) # The projected distance between leader and follower on a 2-D plane.
    azimuth = float(args_tuple_str[3].strip()) # In degree. 0=North(Forward), 90=East(Right), 180=South(back), 270=West(Left).
    print('{} - Calling function fly_follow_leader_onCommand(frame={},height={},radius_2D={},azimuth={}).'.format(time.ctime()), frame, height, radius_2D, azimuth)

    if vehicle.armed:
        # Request leader drone's gps coordinate.
        print('{} - Requesting leader drone\'s gps coordinate...'.format(time.ctime()))
        lat, lon, alt = Client_request_leader_gps(leader_host)
        leader_heading = Client_request_leader_heading(leader_host)
        if (lat != None) and (leader_heading != None):
            print('{} - Leader drone\'s gps coordinate is : lat={}, lon={}, alt={}'.format(time.ctime(), lat, lon, alt))
            if (frame == 'body'):
                # Calculate follower's new location. This location is based on body frame. (0=North, 90=East)
                new_location_gps = new_gps_coord_after_offset_inBodyFrame((lat, lon), radius_2D, leader_heading, azimuth)
                destination = LocationGlobalRelative(new_location_gps[0], new_location_gps[1], alt)
            elif (frame == 'local'):
                # Calculate follower's new location. This location is based on local frame. (0=North, 90=East)
                new_location_gps = new_gps_coord_after_offset_inLocalFrame((lat, lon), radius_2D, azimuth)
                destination = LocationGlobalRelative(new_location_gps[0], new_location_gps[1], alt)
            elif:
                print('{} - Frame string error, neither \'body\' nor \'local\'. fly_follow_leader_onCommand() is not executed!'.format(time.ctime()))
                break
            # Execute fly command.
            vehicle.simple_goto(destination)
            print('{} - After executing fly_follow_leader_onCommand(), vehicle status is:'.format(time.ctime()))
            get_vehicle_state(vehicle)
        else:
            print('{} - Did not get GPS coordinate or leader heading direction, fly_follow_leader_onCommand() is not executed!'.format(time.ctime()))
    else:
        print('{} - Vehicle is not armed.'.format(time.ctime()))
    # Enable other commands.
    __builtin__.status_waitForCommand = True
'''
# ===================================================

# This message has to be sent again and again.


def fly_follow(vehicle, followee_host, frame, height, radius_2D, azimuth):
    print('{} - Calling function fly_follow().'.format(time.ctime()))
    print('     followee_host={}'.format(followee_host))
    print('     frame={}'.format(frame))
    print('     height={}'.format(height))
    print('     radius_2D={}'.format(radius_2D))
    print('     azimuth={}'.format(azimuth))
    if vehicle.armed:
        # Request followee drone's gps coordinate.
        print('{} - Requesting followee drone\'s gps coordinate...'.format(time.ctime()))
        lat, lon, alt = CLIENT_request_gps(followee_host)
        followee_heading = CLIENT_request_heading_direction(followee_host)
        # Calculate destination coordinate based on followee's location.
        if (lat != None) and (followee_heading != None):
            print('{} - Followee drone\'s gps coordinate is : lat={}, lon={}, alt={}'.format(
                time.ctime(), lat, lon, alt))
            if (frame == 'body'):
                # Calculate follower's new location. This location is based on followee's body frame. (0=North, 90=East)
                new_location_gps = new_gps_coord_after_offset_inBodyFrame(
                    (lat, lon), radius_2D, followee_heading, azimuth)
                destination = LocationGlobalRelative(
                    new_location_gps[0], new_location_gps[1], alt)
            elif (frame == 'local'):
                # Calculate follower's new location. This location is based on local frame. (0=North, 90=East)
                new_location_gps = new_gps_coord_after_offset_inLocalFrame(
                    (lat, lon), radius_2D, azimuth)
                destination = LocationGlobalRelative(
                    new_location_gps[0], new_location_gps[1], alt)
            else:
                print(
                    '{} - Frame error, should be \'body\' or \'local\'. fly_follow() is not executed!'.format(time.ctime()))
                return
            # Execute fly command.
            vehicle.simple_goto(destination, groundspeed=5)
            print(
                '{} - After executing fly_follow(), vehicle status is:'.format(time.ctime()))
            get_vehicle_state(vehicle)
        else:
            print('{} - Cannot get followee\'s GPS coordinate or heading direction, fly_follow() is not executed!'.format(time.ctime()))
    else:
        print('{} - Vehicle is not armed.'.format(time.ctime()))

# ===================================================


def takeoff_and_hover(vehicle, hover_target_altitude):
    print('\n')
    print('{} - Executing takeoff_and_hover().'.format(time.ctime()))
    # Take off to target altitude
    vehicle.simple_takeoff(hover_target_altitude)
    # Wait until the vehicle reaches a safe height before processing other command, otherwise the command after Vehicle.simple_takeoff will execute immediately.
    while True:
        print('{} - Current Altitude: {} m'.format(time.ctime(),
              vehicle.location.global_relative_frame.alt))
        get_vehicle_state(vehicle)
        print('\n')
        # Break and return from function just below target altitude.
        if vehicle.location.global_relative_frame.alt >= hover_target_altitude*0.95:
            print('{} - Reached target altitude!\n'.format(time.ctime()))
            break
        time.sleep(1)

# ===================================================

# The takeoff command is asynchronous and can be interrupted if another command arrives before it reaches the target altitude.


def takeoff(vehicle, wait_time):
    print('\n')
    print('{} - Executing takeoff().'.format(time.ctime()))
    # Take off 1 meter. Just take off so we can send other movement command.
    vehicle.simple_takeoff(1)
    time.sleep(wait_time)  # Wait the specified time.

# ===================================================


def return_to_launch(vehicle):
    # If vehicle mode is RTL, it will return to the launch location automatically.
    print('\n')
    print('{} - Returning home...'.format(time.ctime()))
    print('{} - Changing vehicle mode to RTL...'.format(time.ctime()))
    vehicle.mode = VehicleMode('RTL')
    time.sleep(3)  # Wait one second for mode change.
    print('{} - Current vehicle mode is {}'.format(time.ctime(), vehicle.mode))
    while vehicle.armed:
        print('{} - Vehicle is returning, wait for 1 second.'.format(time.ctime()))
        time.sleep(1)
    print('{} - Vehicle has returned home.'.format(time.ctime()))

# ===================================================


def get_vehicle_state(vehicle):
    print('{} - Checking current Vehicle Status:'.format(time.ctime()))
    # Absolute GPS coordinate. Its lat and lon attributes are populated shortly after GPS becomes available. The alt can take several seconds longer to populate (from the barometer).
    print('     Global Location: lat={}, lon={}, alt(above sea leavel)={}'.format(
        vehicle.location.global_frame.lat, vehicle.location.global_frame.lon, vehicle.location.global_frame.alt))
    print('     Global Location (relative altitude): lat={}, lon={}, alt(relative)={}'.format(vehicle.location.global_relative_frame.lat,
          vehicle.location.global_relative_frame.lon, vehicle.location.global_relative_frame.alt))  # GPS coordinate with relative altitude.
    print('     Local Location(NED coordinate): north={}, east={}, down={}'.format(vehicle.location.local_frame.north,
          vehicle.location.local_frame.east, vehicle.location.local_frame.down))  # North east down (NED), also known as local tangent plane (LTP)
    print('     Attitude(radians): Pitch={}, Yaw={}, Roll={}'.format(
        vehicle.attitude.pitch, vehicle.attitude.yaw, vehicle.attitude.roll))  # Pitch, Yaw, and Roll.
    # Current velocity as a three element list [ vx, vy, vz ] (in meter/sec).
    print('     Velocity: Vx={}, Vy={}, Vz={}'.format(
        vehicle.velocity[0], vehicle.velocity[1], vehicle.velocity[2]))
    # GPS Info. fix_type: 0-1, no fix; 2, 2D fix; 3, 3D fix. satellites_visible: Number of satellites visible.
    print('     GPS Info: fix_type={}, num_sat={}'.format(
        vehicle.gps_0.fix_type, vehicle.gps_0.satellites_visible))
    print('     Battery: voltage={}V, current={}A, level={}%'.format(
        vehicle.battery.voltage, vehicle.battery.current, vehicle.battery.level))
    print('     Sonar distance: {} m'.format(vehicle.rangefinder.distance))
    # Current heading in degrees(0~360), where North = 0.
    print('     Heading: {} (degrees from North)'.format(vehicle.heading))
    # Current groundspeed in metres/second (double).This attribute is settable. The set value is the default target groundspeed when moving the vehicle using simple_goto() (or other position-based movement commands).
    print('     Groundspeed: {} m/s'.format(vehicle.groundspeed))
    # Current airspeed in metres/second (double).This attribute is settable. The set value is the default target airspeed when moving the vehicle using simple_goto() (or other position-based movement commands).
    print('     Airspeed: {} m/s'.format(vehicle.airspeed))

# ===================================================
