from math import sqrt
from random import randint, sample
from itertools import combinations, chain

from matplotlib import pyplot

from settings import NUM_LOCATIONS, DOG_NAME_LIST


class TwoDimensionalMap:
    height = 0
    width = 0


class Location:
    name = ""
    x_coord = None
    y_coord = None    

    def __init__(self, name, x, y):
        self.name = name
        self.x_coord = x
        self.y_coord = y


class Neighborhood:
    locations = []
    height = 0
    width = 0

    def __init__(self, width=100, height=100, num_locations=NUM_LOCATIONS):
        self.width = width
        self.height = height

        randomized_names = sample(DOG_NAME_LIST, num_locations)

        self.locations = [
            Location(name, randint(0, width), randint(0, height))
            for name in randomized_names
        ]
        self.hq = Location('Oowlish HQ', self.width/2, self.height/2)

    @property
    def locations_with_hq(self):
        all_locations = list(self.locations)
        all_locations.append(self.hq)
        return all_locations

    def plot_map(self, axes):
        axes.scatter(
            x=[location.x_coord for location in self.locations],
            y=[location.y_coord for location in self.locations],
        )

        for index, location in enumerate(self.locations_with_hq):
            if 'oowlish' in location.name.lower():
                axes.annotate(location.name, (location.x_coord+1, location.y_coord+1))
                axes.scatter(location.x_coord, location.y_coord, s=100)
                return

            axes.annotate(location.name, (location.x_coord+1, location.y_coord+1))

    def plot_possibilities(self):
        possible_pairs = combinations(self.locations_with_hq, 2)
        for location_a, location_b in possible_pairs:
            pyplot.plot(
                [location_a.x_coord, location_b.x_coord],
                [location_a.y_coord, location_b.y_coord],
                '--'
            )

    def plot_distances(self):
        possible_pairs = combinations(self.locations_with_hq, 2)

        def middle_point(location_a, location_b):
            return (location_a.x_coord + location_b.x_coord)/2, (location_a.y_coord + location_b.y_coord)/2
        
        for location_a, location_b in possible_pairs:
            distance = int(self.distance_between(location_a, location_b))
            pyplot.annotate(distance, middle_point(location_a, location_b))

    def configure_plot(self, plot):
        plot.xlim = 0, 100
        plot.xticks([0, 25, 50, 75, 100])
        plot.ylim = 0, 100
        plot.yticks([0, 25, 50, 75, 100])

    @staticmethod
    def distance_between(location_a, location_b):
        x_a, y_a = location_a.x_coord, location_a.y_coord
        x_b, y_b = location_b.x_coord, location_b.y_coord
        
        return sqrt((x_a-x_b)**2 + (y_a-y_b)**2)


if __name__ == "__main__":
    neighborhood = Neighborhood()
    neighborhood.plot_map()
    neighborhood.plot_possibilities()
    neighborhood.plot_distances()
    neighborhood.configure_plot()
    pyplot.show()