from time import time
from concurrent.futures import ThreadPoolExecutor
from random import sample, randint
from itertools import tee

from matplotlib import pyplot

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

            self.best_trainer = self.generation.get_best_trainer()
            best_distance = self.best_trainer.distance

            self.worst_trainer = self.generation.get_worst_trainer()
            worst_distance = self.worst_trainer.distance

            print(f'Best of Generation {generation_number}: {best_distance}')
            print(f'Worst of Generation {generation_number}: {worst_distance}')
            self.best_distances.append(best_distance)

            # if self.has_converged():
            #     break

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

        ranked_trainers = list(generation.trainers)
        ranked_trainers.sort(key=lambda trainer: trainer.distance)

        for trainer_a, trainer_b in pairwise(ranked_trainers):
            child_trainer = Trainer()
            
            child_chromosome = self.crossover(trainer_a, trainer_b)
            self.mutate(child_chromosome)
            child_trainer.path = child_chromosome
            
            new_trainers.append(child_trainer)
            if len(new_trainers) == POPULATION_AMOUNT:
                break
        return new_trainers

    def crossover(self, trainer_a, trainer_b):
        length = len(trainer_a.path)
        
        chromosome_a = trainer_a.path
        chromosome_b = trainer_b.path

        break_point = randint(1, length)
        
        child_chromosome = chromosome_a[0:break_point]
        for allel in chromosome_b:
            if not allel in child_chromosome:
                child_chromosome.append(allel)
            if len(child_chromosome) == NUM_LOCATIONS+1:
                child_chromosome.append(self.neighborhood.hq)
                break

        return child_chromosome


    def mutate(self, chromosome):
        if randint(0, 100) <= 5:
            def swap_allels(position1, position2):
                chromosome[position1], chromosome[position2] = chromosome[position2], chromosome[position1]
            swap_allels(randint(0, len(chromosome)-1), randint(0, len(chromosome)-1))

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
            distance *= 100
            distance += 10000

        self.distance = distance

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
        sim.best_trainer.plot_path(base_axes)
        base_axes.plot()
    
    start = time()
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(sim.run_simulation)
        
        from matplotlib import animation
        print('----HERE-----')
        anim = animation.FuncAnimation(fig, animate, interval=1000)
        pyplot.show()
    end = time()
    
    print("Elapsed time: ", end-start)
    print("Best path: ", [l.name for l in sim.best_trainer.path])

    neighborhood.configure_plot(pyplot)
    sim.best_trainer.plot_path(base_axes)
