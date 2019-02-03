from time import time
from concurrent.futures import ThreadPoolExecutor
from random import sample, randint, random
from itertools import tee

from matplotlib import pyplot, animation

import settings
from city import Neighborhood
from settings import NUM_GENERATIONS, POPULATION_AMOUNT, NUM_LOCATIONS


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


class Simulation:
    def __init__(self, neighborhood, initial_generation):
        self.generation = initial_generation
        self.generation.run_trainers()
        self.neighborhood = neighborhood

        self.best_distances = []

    def run_simulation(self):
        print('--- STARTING SIMULATION --- ')

        for generation_number in range(1, NUM_GENERATIONS+1):
            print(f'\nGeneration number {generation_number}')
            self.generation = Generation(self.neighborhood, self.get_new_trainers(self.generation))
            self.generation.run_trainers()

            this_best_trainer = self.generation.get_best_trainer()
            this_best_distance = this_best_trainer.distance
            if not self.best_distances or this_best_distance < self.best_distance:
                self.best_distance = this_best_distance
                self.best_trainer = this_best_trainer

            print(f'Best across generations: {self.best_distance}')
            print(f'Best of Generation {generation_number}: {this_best_distance}')
            print(f'List of distances: {[int(t.distance) for t in self.generation.ranked_trainers]}')
            self.best_distances.append(this_best_distance)

            # if self.has_converged():
                # break
            

    def has_converged(self):
        if not self.best_distances:
            return False
        
        distances = list(self.best_distances)
        distances.reverse()

        last_result = distances[0]
        for i, distance in enumerate(distances):
            # TODO: better verification of convergence
            if i >= 50:
                return True
            if distance != last_result:
                return False

    def get_new_trainers(self, generation):
        new_trainers = []

        best_previous_trainer = generation.get_best_trainer()
        new_trainers.append(best_previous_trainer)

        if len(set([str(t.printable_path) for t in generation.trainers])) == 1:
            print('Population has converged. Finishing simulation.')
            exit()

        def get_parent_index():
            r = random()
            probs = generation.cumulative_probabilities
            for i in range(len(probs)):
                if probs[i] < r <= probs[i+1]:
                    return i
        
        while True:
            parent_1 = generation.ranked_trainers[get_parent_index()]
            parent_2 = generation.ranked_trainers[get_parent_index()]

            while parent_1.path == parent_2.path:
                parent_2 = generation.ranked_trainers[get_parent_index()]

            child_a, child_b = Trainer(), Trainer()
            
            child_a_path, child_b_path = self.crossover(parent_1, parent_2)
            self.mutate(child_a_path)
            self.mutate(child_b_path)
            child_a.path, child_b.path = child_a_path, child_b_path
            
            new_trainers.extend([child_a, child_b])
            if len(new_trainers) >= POPULATION_AMOUNT:
                new_trainers = new_trainers[0:POPULATION_AMOUNT+1]
                break

        return new_trainers

    def crossover(self, trainer_a, trainer_b):
        length = len(trainer_a.path)
        
        chromosome_a = trainer_a.path
        chromosome_b = trainer_b.path

        random_slice = [randint(1, length-1), randint(1, length-1)]
        random_slice.sort()
        
        
        def get_child_chromosome(base_parent, secondary_parent):
            child_chromosome = [None] * (NUM_LOCATIONS + 2)
            child_chromosome[random_slice[0]:random_slice[1]] = base_parent[random_slice[0]:random_slice[1]]

            for index, allel in enumerate(child_chromosome):
                if allel:
                    continue
                if index == 0:
                    child_chromosome[index] = base_parent[index]
                elif index == NUM_LOCATIONS+1:
                    child_chromosome[index] = base_parent[index]
                    break
                else:
                    child_chromosome[index] = next(allel_b for allel_b in secondary_parent if not allel_b in child_chromosome)
            
            return child_chromosome

        return get_child_chromosome(chromosome_a, chromosome_b), get_child_chromosome(chromosome_b, chromosome_a)


    def mutate(self, chromosome):
        def swap_allels(position1, position2):
            chromosome[position1], chromosome[position2] = chromosome[position2], chromosome[position1]
        
        random_int = randint(0, 100)
        # if random_int <= settings.CHANCE_SEQUENTIAL_SWAP_MUTATION:
        #     base_index = randint(1, len(chromosome)-1)
        #     swap_allels(base_index - 1, base_index)
        if random_int <= settings.CHANCE_RANDOM_SWAP_MUTATION:
            swap_allels(randint(1, len(chromosome)-2), randint(1, len(chromosome)-2))


class Generation:
    def __init__(self, neighborhood=None, trainers=[]):
        self.trainers = trainers
        self.neighborhood = neighborhood

    def setup_random_generation(self, num_trainers):
        for _ in range(num_trainers):
            trainer = Trainer()
            trainer.set_random_path(neighborhood)
            self.trainers.append(trainer)

    def run_trainers(self):
        for trainer in self.trainers:
            trainer.calculate_distance()

    @property
    def total_distance(self):
        return sum([trainer.distance for trainer in self.trainers])

    @property
    def total_fitness(self):
        return sum([trainer.fitness for trainer in self.trainers])

    @property
    def ranked_trainers(self):
        ranked_trainers = list(self.trainers)
        ranked_trainers.sort(key=lambda trainer: trainer.distance)
        return ranked_trainers

    @property
    def individual_probabilities(self):
        probability_dist = []
        for trainer in self.ranked_trainers:
            probability_dist.append(trainer.fitness/self.total_fitness)
        return probability_dist

    @property
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


class Trainer:
    path = []

    def set_random_path(self, neighborhood):
        self.path = sample(neighborhood.locations, NUM_LOCATIONS)
        self.path.insert(0, neighborhood.hq)
        self.path.append(neighborhood.hq)

    def calculate_distance(self):
        if not self.path:
            raise Exception('Trainer path is not set.')
        
        distance = 0
        for location_a, location_b in pairwise(self.path):
            distance += Neighborhood.distance_between(location_a, location_b)

        def should_penalize():
            if not len(set(self.path)) == NUM_LOCATIONS+1:
                return True
            elif not 'oowlish' in self.path[0].name.lower():
                return True
            elif not 'oowlish' in self.path[-1].name.lower():
                return True
            return False
        
        if should_penalize():
            import pdb; pdb.set_trace()
            distance *= 100
            distance += 10000

        self.distance = distance

    @property
    def fitness(self):
        return 1/self.distance

    @property
    def printable_path(self):
        return [location.name for location in self.path]

    def plot_path(self, axes):
        x = [location.x_coord for location in self.path]
        y = [location.y_coord for location in self.path]
        axes.plot(x, y)


if __name__ == '__main__':
    neighborhood = Neighborhood()

    fig = pyplot.figure()
    base_axes = fig.add_subplot(111)
    neighborhood.plot_map(base_axes)

    generation = Generation()
    generation.neighborhood = neighborhood
    generation.setup_random_generation(POPULATION_AMOUNT)
    sim = Simulation(neighborhood, generation)

    def animate(i):
        base_axes.clear()
        neighborhood.plot_map(base_axes)
        try:
            sim.best_trainer.plot_path(base_axes)
        except AttributeError:
            pass
        base_axes.plot()
    # sim.run_simulation()
    start = time()
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(sim.run_simulation)
        anim = animation.FuncAnimation(fig, animate, interval=1000)
        pyplot.show()
    end = time()
    
    print("Elapsed time: ", end-start)
    print("Best path: ", [l.name for l in sim.best_trainer.path])

    neighborhood.configure_plot(pyplot)
    sim.best_trainer.plot_path(base_axes)
