from time import time
from concurrent.futures import ThreadPoolExecutor
from random import randint, random

from matplotlib import pyplot, animation

import settings
from trainer import Trainer, Generation
from city import Neighborhood

class Simulation:
    def __init__(self, neighborhood, initial_generation):
        self.generation = initial_generation
        self.generation.run_trainers()
        self.neighborhood = neighborhood

        self.best_distances = []

    def run_simulation(self):
        print('--- STARTING SIMULATION --- ')

        for generation_number in range(1, settings.NUM_GENERATIONS+1):
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
            # TODO: better if above
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

            child_a, child_b = Trainer(self.neighborhood), Trainer(self.neighborhood)
            
            child_a_path, child_b_path = self.crossover(parent_1, parent_2)
            self.mutate(child_a_path)
            self.mutate(child_b_path)
            child_a.path, child_b.path = child_a_path, child_b_path
            
            new_trainers.extend([child_a, child_b])
            if len(new_trainers) >= settings.POPULATION_AMOUNT:
                new_trainers = new_trainers[0:settings.POPULATION_AMOUNT+1]
                break

        return new_trainers

    def crossover(self, trainer_a, trainer_b):
        length = len(trainer_a.path)
        
        chromosome_a = trainer_a.path
        chromosome_b = trainer_b.path

        random_slice = [randint(0, length), randint(0, length)]
        random_slice.sort()
        
        def get_child_chromosome(base_parent, secondary_parent):
            child_chromosome = [None] * settings.NUM_LOCATIONS
            child_chromosome[random_slice[0]:random_slice[1]] = base_parent[random_slice[0]:random_slice[1]]

            for index, allel in enumerate(child_chromosome):
                if allel:
                    continue
                child_chromosome[index] = next(allel_b for allel_b in secondary_parent if not allel_b in child_chromosome)
            
            return child_chromosome

        return get_child_chromosome(chromosome_a, chromosome_b), get_child_chromosome(chromosome_b, chromosome_a)

    def mutate(self, chromosome):
        def swap_allels(position1, position2):
            chromosome[position1], chromosome[position2] = chromosome[position2], chromosome[position1]
        
        random_int = randint(0, 100)
        if random_int <= settings.CHANCE_SEQUENTIAL_SWAP_MUTATION:
            base_index = randint(1, len(chromosome)-1)
            swap_allels(base_index - 1, base_index)
        if random_int <= settings.CHANCE_RANDOM_SWAP_MUTATION:
            swap_allels(randint(1, len(chromosome)-2), randint(1, len(chromosome)-2))


if __name__ == '__main__':
    neighborhood = Neighborhood()

    fig = pyplot.figure()
    base_axes = fig.add_subplot(111)
    neighborhood.plot_map(base_axes)

    generation = Generation(neighborhood=neighborhood)
    generation.setup_random_generation(settings.POPULATION_AMOUNT)
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
