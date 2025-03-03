#! /usr/bin/python

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import time
import drivers
import face_recognition
import imutils
import pickle
import time
import cv2

#API to send Notification
from pushbullet import Pushbullet

API_key = '' # Adicione o TOKEN

pb = Pushbullet(API_key)


#Instanciando Drivers()
#Caso precise usar a biblioteca, usar display.

display = drivers.Lcd()
display.lcd_display_string("Carregando...", 1)

#Initialize 'currentname' to trigger only when a new person is identified.
currentname = "unknown"
#Determine faces from encodings.pickle file model created from train_model.py
encodingsP = "encodings.pickle"

# load the known faces and embeddings along with OpenCV's Haar
# cascade for face detection
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(encodingsP, "rb").read(),encoding='latin1')

vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)

# start the FPS counter
fps = FPS().start()

apeared = []

# loop over frames from the video file stream
while True:
	# grab the frame from the threaded video stream and resize it
	# to 500px (to speedup processing)
	frame = vs.read()
	# Detect the fce boxes
	boxes = face_recognition.face_locations(frame)
	# compute the facial embeddings for each face bounding box
	encodings = face_recognition.face_encodings(frame, boxes)
	names = []
	
	display.lcd_clear()
	display.lcd_display_string("PROCURANDO ROSTO", 1)
	display.lcd_display_string("CADASTRADO...", 2)
	# loop over the facial embeddings
	for encoding in encodings:
		# attempt to match each face in the input image to our known
		# encodings
		matches = face_recognition.compare_faces(data["encodings"],
			encoding)
		name = "Unknown" #if face is not recognized, then print Unknown

		# check to see if we have found a match
		if True in matches:
			# find the indexes of all matched faces then initialize a
			# dictionary to count the total number of times each face
			# was matched
			matchedIdxs = [i for (i, b) in enumerate(matches) if b]
			counts = {}

			# loop over the matched indexes and maintain a count for
			# each recognized face face
			for i in matchedIdxs:
				name = data["names"][i]
				counts[name] = counts.get(name, 0) + 1

			# determine the recognized face with the largest number of votes
			name = max(counts, key=counts.get)

			#If someone in your dataset is identified, print their name on the screen
			if currentname != name:
				currentname = name
				print(currentname)

				if(currentname not in apeared):
					apeared.append(currentname)

					#Enviando Notificação
					push = pb.push_note("Pessoa Reconhecida", currentname + " está na porta!" )

					# Tirando foto para notificação
					img_name = currentname + "image.jpg"
					cv2.imwrite(img_name, frame)
					print('Taking a picture.')
					with open(img_name, "rb") as pic:
						file_data = pb.upload_file(pic, "picture.jpg")
					push = pb.push_file(**file_data)

		# update the list of names
		names.append(name)

	# loop over the recognized faces
	for ((top, right, bottom, left), name) in zip(boxes, names):
		# draw the predicted face name on the image - color is in BGR
		cv2.rectangle(frame, (left, top), (right, bottom),
			(0, 255, 225), 2)
		y = top - 15 if top - 15 > 15 else top + 15
		cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
			.8, (0, 255, 255), 2)

		#Escrevendo no LCD	
		if(name != "Unknown"):
			display.lcd_clear()
			display.lcd_display_string("Reconhecid@: ", 1)
			display.lcd_display_string(name, 2)
	
	# display the image to our screen
	cv2.imshow("Facial Recognition is Running", frame)
	key = cv2.waitKey(1) & 0xFF

	# quit when 'q' key is pressed
	if key == ord("q"):
		break

	# update the FPS counter
	fps.update()
# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()

print("Cleaning up!")
display.lcd_clear()
