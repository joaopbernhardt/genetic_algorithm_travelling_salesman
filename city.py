from math import sqrt
from random import randint, sample
from itertools import combinations, chain

from matplotlib import pyplot

from settings import NUM_LOCATIONS, DOG_NAME_LIST


class Location:
    def __init__(self, name, x, y):
        self.name = name
        self.x_coord = x
        self.y_coord = y


class Neighborhood:

    def __init__(self, width=100, height=100, num_locations=NUM_LOCATIONS):
        self.width = width
        self.height = height
        self.locations = []
        self.cached_distances = {}

        randomized_names = sample(DOG_NAME_LIST, num_locations)

        def uncentered_random_coord():
            coord = 0
            while not coord and not 40 < coord < 60:
                coord = randint(0, width)
            return coord

        self.locations = [
            Location(name, uncentered_random_coord(), uncentered_random_coord())
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
                axes.scatter(location.x_coord, location.y_coord, s=150)
                return

            axes.annotate(location.name, (location.x_coord+1, location.y_coord+1))

    def plot_possibilities(self, axes):
        possible_pairs = combinations(self.locations_with_hq, 2)
        for location_a, location_b in possible_pairs:
            axes.plot(
                [location_a.x_coord, location_b.x_coord],
                [location_a.y_coord, location_b.y_coord],
                '--'
            )

    def plot_distances(self, axes):
        possible_pairs = combinations(self.locations_with_hq, 2)

        def middle_point(location_a, location_b):
            return (location_a.x_coord + location_b.x_coord)/2, (location_a.y_coord + location_b.y_coord)/2
        
        for location_a, location_b in possible_pairs:
            distance = int(self.distance_between(location_a, location_b))
            axes.annotate(distance, middle_point(location_a, location_b))

    def configure_plot(self, plot):
        plot.xlim = 0, 100
        plot.xticks([0, 25, 50, 75, 100])
        plot.ylim = 0, 100
        plot.yticks([0, 25, 50, 75, 100])

    def distance_between(self, location_a, location_b):
        cache_name = location_a.name+location_b.name
        if cache_name in self.cached_distances:
            return self.cached_distances[cache_name]
        
        x_a, y_a = location_a.x_coord, location_a.y_coord
        x_b, y_b = location_b.x_coord, location_b.y_coord
        
        self.cached_distances[cache_name] = sqrt((x_a-x_b)**2 + (y_a-y_b)**2)
        return self.cached_distances[cache_name]


if __name__ == "__main__":
    fig = pyplot.figure()
    axes = fig.add_subplot(111)

    neighborhood = Neighborhood()
    neighborhood.plot_map(axes)
    neighborhood.plot_possibilities(axes)
    pyplot.show()
    # neighborhood.plot_distances(axes)
    # neighborhood.configure_plot(pyplot)
    # pyplot.show()