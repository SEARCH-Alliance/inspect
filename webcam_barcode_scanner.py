import cv2
import time
import cv2
import numpy as np
import zbar

scanner = zbar.Scanner()


def detect(image):
    results = scanner.scan(image)
    if len(results) == 0:
        return [], []
    else:
        pass
    boxes = []
    data = []
    for result in results:
        boxes.append(result.position)
        data.append(result.data)
    return boxes, data


# live window version
def barcode_capture():
    # if the video path was not supplied, grab the reference to the
    # camera
    vs = cv2.VideoCapture(0)
    time.sleep(2.0)
    # keep looping over the frames
    barcodes = []
    while True:
        if len(barcodes) > 0:
            break
        else:
            # grab the current frame and then handle if the frame is returned
            check, frame = vs.read()

            # if webcam is buggy, break
            if frame is None:
                break
            # detect the barcode in the image
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            boxes, data = detect(img)
            if len(data) == 0:
                boxes = None
            else:
                pass
            if boxes is not None:
                for i in data:
                    if i.decode('utf-8') not in barcodes:
                        print(i.decode('utf-8'))
                        barcodes.append(i.decode('utf-8'))
                    else:
                        pass
            # if a barcode was found, draw a bounding box on the frame
            if boxes is not None:
                for box in boxes:
                    # print(box)
                    frame = cv2.line(frame, box[0], box[1], (255, 0, 0), 5)
                    frame = cv2.line(frame, box[1], box[2], (255, 0, 0), 5)
                    frame = cv2.line(frame, box[2], box[3], (255, 0, 0), 5)
                    frame = cv2.line(frame, box[3], box[0], (255, 0, 0), 5)
            # show the frame and record if the user presses a key
            cv2.startWindowThread()
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1) & 0xFF
            # if the 'q' key is pressed, stop the loop
            if key == ord("q"):
                vs.release()
                cv2.destroyAllWindows()
                cv2.waitKey(1)
                break
    return barcodes


if __name__ == "__main__":
    barcode_capture()
