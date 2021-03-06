from random import sample
from itertools import tee

import settings


class cached_property:
    """
    Saves the result of an object's @property into the object itself,
    effectively caching the value. Returns it if available on subsequent calls. 
    """
    def __init__(self, function):
        self.function = function

    def __get__(self, obj, cls):
        cached_name = 'cached_'+self.function.__name__

        if not hasattr(obj, cached_name):
            setattr(obj, cached_name, self.function(obj))

        return getattr(obj, cached_name)


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    # Recipe as seen in itertools module documentation.
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


class Individual:
    """
    This class is the "Individual" in Genetic Algorithm's terms.
    The "path" attribute is the chromosome, while the locations are the genes.
    """
    def __init__(self, world, path=set()):
        self.world = world
        self.path = path

    @cached_property
    def full_path(self):
        return [self.world.hq, *self.path, self.world.hq]

    @cached_property
    def distance(self):
        if not self.path:
            raise Exception('Individual path is not set.')
        
        distance = 0
        for location_a, location_b in pairwise(self.full_path):
            distance += self.world.distance_between(location_a, location_b)

        def should_penalize():
            if not len(set(self.path)) == settings.NUM_LOCATIONS:
                # Path has to contain all locations
                return True
            return False
        
        if should_penalize():
            # Due to the way the crossovers, mutations etc were done,
            # it is not expected to have penalizations.
            # Set a debugger for easily investigating if this happens.
            import pdb; pdb.set_trace()
            distance *= 100
            distance += 10000

        return distance

    @cached_property
    def fitness(self):
        """
        The smaller the distance of this individual, the fitter it is.
        """
        return 1/self.distance

    @cached_property
    def printable_path(self):
        return [location.name for location in self.full_path]

    @staticmethod
    def have_the_same_path(individual_1, individual_2):
        """
        Checks if paths are either equal or symmetric
        """
        reversed_2 = list(individual_2.path)
        reversed_2.reverse()
        return individual_1.path == individual_2.path or individual_1 == reversed_2

    def set_random_path(self):
        self.path = sample(self.world.locations, settings.NUM_LOCATIONS)

    def plot_path(self, axes):
        x = [location.x_coord for location in self.full_path]
        y = [location.y_coord for location in self.full_path]
        axes.plot(x, y)


class Generation:
    """
    Collection of individuals.
    Contains important methods for evaluating the generation,
    such as the probabilities of selection of an individual for being
    a parent.
    """
    def __init__(self, world=None, individuals=[], random=True):
        self.individuals = individuals
        self.world = world
        if random:
            self.setup_random_generation(settings.POPULATION_AMOUNT)

    @cached_property
    def total_distance(self):
        return sum([individual.distance for individual in self.individuals])

    @cached_property
    def total_fitness(self):
        return sum([individual.fitness for individual in self.individuals])

    @cached_property
    def ranked_individuals(self):
        """
        Returns a sorted iterable beginning with the best individual.
        """
        ranked_individuals = list(self.individuals)
        ranked_individuals.sort(key=lambda individual: individual.fitness, reverse=True)
        return ranked_individuals

    @cached_property
    def individual_probabilities(self):
        probability_dist = []
        if "roulette" in settings.SELECTION_METHOD.lower():
            for individual in self.ranked_individuals:
                probability_dist.append(individual.fitness/self.total_fitness)
        else:
            raise Exception('Invalid selection method.')
        # TODO: fix linear rank probabilities below
        # elif "rank" in settings.SELECTION_METHOD.lower():
        #     total = sum([i for i in range(1, len(self.individuals)+1)])
        #     for index, individual in enumerate(self.ranked_individuals):
        #         probability_dist.append((index+1)/total)
        
        return probability_dist

    @cached_property
    def cumulative_probabilities(self):
        """
        Iteratively sums each individual's probabilities to build a
        iterable where the first value is 0, the last is 100%. 
        """
        probs = [0]
        
        i = 0
        for individual_prob in self.individual_probabilities:
            probs.append(individual_prob + probs[i])
            i += 1
        
        # Sanity checks
        assert probs[0] == 0  # first term should always be 0
        assert 0.9999 <= probs[-1] <= 1.0001  # last term should always be 100%
        
        return probs

    def setup_random_generation(self, num_individuals):
        for _ in range(num_individuals):
            individual = Individual(self.world)
            individual.set_random_path()
            self.individuals.append(individual)

    def get_best_individual(self):
        min_distance = min([individual.distance for individual in self.individuals])
        return next(individual for individual in self.individuals if individual.distance == min_distance)

    def get_worst_individual(self):
        max_distance = max([individual.distance for individual in self.individuals])
        return next(individual for individual in self.individuals if individual.distance == max_distance)

    def get_elite(self, amount):
        """
        Chooses the best `amount` unique individuals that have different paths.
        """
        elite = []
        for individual in self.ranked_individuals:
            if len(elite) == amount:
                break

            # Checks if this individual is already in elite
            for this_elite in elite:
                if Individual.have_the_same_path(individual, this_elite):
                    continue

            elite.append(individual)
        return elite
