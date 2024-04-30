import requests
import time
import serial
import math

# =========
# settings

# Octoprint API key
api_key = "<API_KEY>"
# Octoprint base url
base_url = "http://127.0.0.1:5000/"

# Arduino serial port
serial_port = "/dev/ttyACM0"

# mode (True for current, False for voltage)
current_mode = True
# target current in mA
target_current = 5
# target voltage in V
target_voltage = 3
# target duration in seconds
duration = 10
# distance between anode and cathode in mm
diff_z = 2

# machine limits
max_z = 25.0
min_z = 19.0
max_y = 133.0
min_y = 101.0
max_x = 104.0
min_x = 72.0

# number of points on each circle
points = 8
# distance between the radius of each circle
inc_r = 2

# =========

# find the actual min_z
min_z = min_z + diff_z
# find the middle
cx = min_x + (max_x - min_x) / 2
cy = min_y + (max_y - min_y) / 2
# find the diameter
d = min(max_x - min_x, max_y - min_y)
# find the angle between each points
inc_theta = 360.0 / points

try:
	# connections
	ser = serial.Serial(serial_port, 9600)
	print("Serial connected to", ser.name)

	# send reset command to arduino
	ser.write("r".encode())

	# create the request session so we don't have to repeat the header
	s = requests.Session()
	s.headers.update({ "X-Api-Key": api_key, "Content-Type": "application/json" })
	print_head_endpoint = "api/printer/printhead"

	# log file
	f = open("log.txt", "w")
	f.write("Staring Time " + str(time.time()) + "\n")
	# log settings
	f.write("current_mode " + str(current_mode) + "\n")
	f.write("target_current " + str(target_current) + "\n")
	f.write("target_voltage " + str(target_voltage) + "\n")
	f.write("duration " + str(duration) + "s\n")
	f.write("diff_z " + str(diff_z) + "mm\n")
	f.write("points " + str(points) + "\n")
	f.write("inc_r " + str(inc_r) + "mm\n")
	f.write("====================================\n")

	# move the head to the right height
	res = s.post(base_url + print_head_endpoint, json={ "command": "jog", "z": max_z, "absolute": True })
	print("Up", res)
	time.sleep(10)

	# polar coord
	r = inc_r
	theta = 0

	while True:
		# if we finished one circle, move the radius out to begin the next circle
		if theta >= 360:
			theta = 0
			r = r + inc_r

		# if we are at the outer most circle, stop the loop
		if r > d/2:
			res = s.post(base_url + print_head_endpoint, json={ "command": "jog", "z": max_z, "absolute": True })
			print("Up", res)
			time.sleep(10)
			break

		# convert polar to cartesian
		x = cx + r * math.cos(math.radians(theta))
		y = cy + r * math.sin(math.radians(theta))
		print("x", x, "y", y)
		f.write("\nPoint (x: " + str(x) + ", y: " + str(y) + ")\n")

		# move the head to calculated position
		res = s.post(base_url + print_head_endpoint, json={ "command": "jog", "x": x, "y": y, "absolute": True })
		print("Move", res)
		time.sleep(1)

		# move the head down
		res = s.post(base_url + print_head_endpoint, json={ "command": "jog", "z": min_z, "absolute": True })
		print("Down", res)
		time.sleep(2)

		# signal the arduino to start electroplating
		if current_mode:
			ser.write(("c " + str(target_current)).encode())
		else:
			ser.write(("v " + str(target_voltage)).encode())
		print("on")

		# record the start time so we know how long it has been
		start = time.time()
		while time.time() - start < duration: # loop until time has reached the set duration
			l = ser.readline().decode()
			print(l, end="")
			f.write(l)

		# signal the arduino to stop electroplating
		ser.write("f".encode())
		print("off")
		time.sleep(0.5)

		# move the head up
		res = s.post(base_url + print_head_endpoint, json={ "command": "jog", "z": max_z, "absolute": True })
		print("Up", res)
		time.sleep(2)

		# increase the angle
		theta = theta + inc_theta

# if Ctrl-C detected quit gracefully
except KeyboardInterrupt:
	print("Ctrl-C detected, quitting")
finally:
	ser.close()
	f.close()
