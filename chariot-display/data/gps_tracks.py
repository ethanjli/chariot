"""Classes representing GPS tracks."""
import collections

import dateutil.parser
import pykml.parser

import data

_XML_NS = {
    'kml': 'http://www.opengis.net/kml/2.2',
    'gx': 'http://www.google.com/kml/ext/2.2',
    'atom': 'http://www.w3.org/2005/Atom'
}

GPSSample = collections.namedtuple('GPSSample', ['time', 'coord'])

class Track(object):
    def __init__(self):
        self.timestamps = None
        self.coordinates = None
        self.samples = None
        self._bounds = None

    def load_from_kml(self, path):
        with open(path) as f:
            tree = pykml.parser.parse(f)
        root = tree.getroot()
        self.parse_mytracks(root.Document)

    def parse_mytracks(self, document):
        tracks = document.Folder
        track = tracks.find('.//gx:Track', namespaces=_XML_NS)
        timestamps = track.find('./kml:when', namespaces=_XML_NS)
        coordinates = track.find('./gx:coord', namespaces=_XML_NS)
        self.timestamps = list(self.parse_timestamps(timestamps))
        self.coordinates = list(self.parse_coordinates(coordinates))
        self.samples = list(GPSSample(time, coord)
                            for (time, coord) in zip(self.timestamps, self.coordinates))

    def parse_timestamps(self, timestamps):
        return (dateutil.parser.parse(timestamp.text) for timestamp in timestamps)

    def parse_coordinates(self, coordinates):
        return (tuple(float(value) for value in coordinate.text.split(' '))
                for coordinate in coordinates)

    @property
    def longitudes(self):
        return zip(*self.coordinates)[0]

    @property
    def latitudes(self):
        return zip(*self.coordinates)[1]

    @property
    def longitude_deltas(self):
        return [t - s for s, t in zip(self.longitudes, self.longitudes[1:])]

    @property
    def latitude_deltas(self):
        return [t - s for s, t in zip(self.latitudes, self.latitudes[1:])]

    @property
    def coordinates_and_deltas(self):
        return list(zip(self.longitudes, self.latitudes,
                        self.longitude_deltas, self.latitude_deltas))

    def __len__(self):
        if self.timestamps is not None:
            return len(self.timestamps)
        return None

    @property
    def bounds(self):
        if self._bounds is None:
            self._bounds = (min(self.longitudes), max(self.longitudes),
                            min(self.latitudes), max(self.latitudes))
        return self._bounds

class KMLSequence(data.DataLoader, data.DataGenerator, Track):
    """Interface for a GPS sequence in a track KML file."""
    def __init__(self, path):
        super(KMLSequence, self).__init__()
        self.path = path
        self._samples = None

    # From DataLoader

    def load(self):
        self.load_from_kml(self.path)
        self._samples = iter(self.samples)

    # From DataGenerator

    def reset(self):
        self._samples = iter(self.samples)

    def next(self):
        return next(self._samples)

