import cv2

import data

# Image Display

class ImageDisplayer(data.images.ImageLoaderClient):
    def __init__(self, image_rotation_angle, *args, **kwargs):
        super(ImageDisplayer, self).__init__(*args, **kwargs)
        self.windows = []
        self.updated_state = False
        self.images = []
        self.image_rotation_angle = image_rotation_angle
        self.image_rotation = None

    def redraw(self):
        # This needs to be called in the main thread for thread-safety!
        for (index, image) in enumerate(self.images):
            cv2.imshow(self.windows[index], cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        self.updated_state = False

    # From DataLoader

    def load(self):
        super(ImageDisplayer, self).load()

        # Initialize rotation
        if self.image_rotation_angle:
            image_shape = self.get_image_shape()
            self.image_rotation = cv2.getRotationMatrix2D((image_shape[0] / 2, image_shape[0] / 2), self.image_rotation_angle, 1)

        # Initialize windows
        self.windows = [str(sequence) for sequence in self.sequences]
        cv2.startWindowThread()
        for window in self.windows:
            cv2.namedWindow(window, cv2.WINDOW_NORMAL)

    def stop_loading(self):
        super(ImageDisplayer, self).stop_loading()
        for window in self.windows:
            cv2.destroyWindow(window)

    # From DataGenerator

    def reset(self):
        super(ImageDisplayer, self).reset()
        self.updated_state = False
        self.windows = []
        self.images = []

    def next(self):
        self.images = super(ImageDisplayer, self).next()
        if self.image_rotation is not None:
            self.images = [cv2.warpAffine(image, self.image_rotation, self.get_image_shape()) for image in self.images]
        self.updated_state = True
