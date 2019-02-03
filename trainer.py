from random import sample
from itertools import tee

import settings


class cached_property:
    def __init__(self, function):
        self.function = function

    def __get__(self, obj, cls):

        cached_name = 'cached_'+self.function.__name__

        if not hasattr(obj, cached_name):
            setattr(obj, cached_name, self.function(obj))

        return getattr(obj, cached_name)


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


class Generation:
    def __init__(self, neighborhood=None, trainers=[]):
        self.trainers = trainers
        self.neighborhood = neighborhood

    def setup_random_generation(self, num_trainers):
        for _ in range(num_trainers):
            trainer = Trainer(self.neighborhood)
            trainer.set_random_path()
            self.trainers.append(trainer)

    @cached_property
    def total_distance(self):
        return sum([trainer.distance for trainer in self.trainers])

    @cached_property
    def total_fitness(self):
        return sum([trainer.fitness for trainer in self.trainers])

    @cached_property
    def ranked_trainers(self):
        ranked_trainers = list(self.trainers)
        ranked_trainers.sort(key=lambda trainer: trainer.fitness, reverse=True)
        return ranked_trainers

    @cached_property
    def individual_probabilities(self):
        probability_dist = []
        if "roulette" in settings.SELECTION_METHOD.lower():
            for trainer in self.ranked_trainers:
                probability_dist.append(trainer.fitness/self.total_fitness)
        else:
            raise Exception('Invalid selection method.')
        # TODO: fix linear rank probabilities below
        # elif "rank" in settings.SELECTION_METHOD.lower():
        #     total = sum([i for i in range(1, len(self.trainers)+1)])
        #     for index, trainer in enumerate(self.ranked_trainers):
        #         probability_dist.append((index+1)/total)
        
        return probability_dist

    @cached_property
    def cumulative_probabilities(self):
        probs = [0]
        
        i = 0
        for individual_prob in self.individual_probabilities:
            probs.append(individual_prob + probs[i])
            i += 1
        return probs

    def get_best_trainer(self):
        min_distance = min([trainer.distance for trainer in self.trainers])
        return next(trainer for trainer in self.trainers if trainer.distance == min_distance)

    def get_worst_trainer(self):
        max_distance = max([trainer.distance for trainer in self.trainers])
        return next(trainer for trainer in self.trainers if trainer.distance == max_distance)

    def get_elite(self, amount):
        """
        Chooses the best unique trainers (different paths)
        """
        elite = []
        for trainer in self.ranked_trainers:
            if len(elite) == amount:
                break
            if not trainer.path in [t.path for t in elite]:
                elite.append(trainer)
        return elite


class Trainer:

    def __init__(self, neighborhood, path=[]):
        self.neighborhood = neighborhood
        self.path = path

    @cached_property
    def full_path(self):
        return [self.neighborhood.hq, *self.path, self.neighborhood.hq]

    @cached_property
    def distance(self):
        if not self.path:
            raise Exception('Trainer path is not set.')
        
        distance = 0
        for location_a, location_b in pairwise(self.full_path):
            distance += self.neighborhood.distance_between(location_a, location_b)

        def should_penalize():
            if not len(set(self.path)) == settings.NUM_LOCATIONS:
                # Path has to contain all locations
                return True
            return False
        
        if should_penalize():
            import pdb; pdb.set_trace()
            distance *= 100
            distance += 10000

        return distance

    @cached_property
    def fitness(self):
        return 1/self.distance

    @cached_property
    def printable_path(self):
        return [location.name for location in self.full_path]

    def set_random_path(self):
        self.path = sample(self.neighborhood.locations, settings.NUM_LOCATIONS)

    def plot_path(self, axes):
        x = [location.x_coord for location in self.full_path]
        y = [location.y_coord for location in self.full_path]
        axes.plot(x, y)
