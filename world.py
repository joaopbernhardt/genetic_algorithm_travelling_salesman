from math import sqrt, factorial
from random import randint, sample
from itertools import combinations, chain
from decimal import Decimal

from matplotlib import pyplot

from settings import NUM_LOCATIONS, LOCATION_NAME_LIST


class Location:
    """
    2-coordinate point in the map.
    """
    def __init__(self, name, x, y):
        self.name = name
        self.x_coord = x
        self.y_coord = y


class World:
    """
    Mainly a collection of Locations, although also contains some
    util methods.
    """
    def __init__(self, width=100, height=100, num_locations=NUM_LOCATIONS):
        self.width = width
        self.height = height
        self.locations = []
        self.cached_distances = {}

        randomized_names = sample(LOCATION_NAME_LIST, num_locations)

        self.locations = [
            Location(name, randint(0, width), randint(0, height))
            for name in randomized_names
        ]
        self.hq = Location('Original city', self.width/2, self.height/2)

    @property
    def locations_with_hq(self):
        all_locations = list(self.locations)
        all_locations.append(self.hq)
        return all_locations

    @property
    def num_possible_solutions(self):
        """
        Search space is the amount of permutations of locations,
        that is, it's factorial.
        Having specific points on the edges do not affect this,
        i.e. beginning and ending are pre-set.
        """
        return factorial(len(self.locations))

    def distance_between(self, location_a, location_b):
        """
        Remember the Pythagorean theorem? Exactly.
        Caches the value since this will be called many times.
        """
        cache_name = location_a.name+location_b.name
        if cache_name in self.cached_distances:
            return self.cached_distances[cache_name]
        
        x_a, y_a = location_a.x_coord, location_a.y_coord
        x_b, y_b = location_b.x_coord, location_b.y_coord
        
        self.cached_distances[cache_name] = sqrt((x_a-x_b)**2 + (y_a-y_b)**2)
        return self.cached_distances[cache_name]

    def plot_map(self, axes):
        axes.scatter(
            x=[location.x_coord for location in self.locations],
            y=[location.y_coord for location in self.locations],
        )

        for index, location in enumerate(self.locations_with_hq):
            if location.name == self.hq.name:
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

    def configure_plot(self, plot, gen=None):
        def format_e(n):
            return '{:.2e}'.format(n)
        title = f'{NUM_LOCATIONS} locations, {format_e(self.num_possible_solutions)} possibilities.'
        if gen:
            title += f" Generation {gen}"
        plot.title(title)
        plot.xlim = 0, 100
        plot.xticks([0, 25, 50, 75, 100])
        plot.ylim = 0, 100
        plot.yticks([0, 25, 50, 75, 100])


if __name__ == "__main__":
    fig = pyplot.figure()
    axes = fig.add_subplot(111)

    world = World()
    world.plot_map(axes)
    world.plot_possibilities(axes)
    world.plot_distances(axes)
    world.configure_plot(pyplot)

    pyplot.show()