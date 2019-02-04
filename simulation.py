import time
from concurrent.futures import ThreadPoolExecutor
from random import randint, random, shuffle

from matplotlib import pyplot, animation

import settings
from trainer import Trainer, Generation
from city import Neighborhood


class Simulation:
    """
    Controller class for the simulation in general, that is,
    contains the loop which creates and evaluates generations,
    performs the crossovers, mutations.
    """
    def __init__(self, neighborhood, initial_generation):
        self.generation = initial_generation
        self.neighborhood = neighborhood

        self.best_distances = []  # Best results for each generation

    def run_simulation(self):
        print('--- STARTING SIMULATION --- ')

        for generation_number in range(1, settings.NUM_GENERATIONS+1):
            # Creates a new generation based on the previous one
            self.generation = Generation(self.neighborhood, self.get_new_trainers(self.generation))

            # This generation's results
            this_best_trainer = self.generation.get_best_trainer()
            this_best_distance = this_best_trainer.distance
            
            # Saves the result if it's the best one so far, across generations
            if generation_number == 1 or this_best_distance < self.best_distance:
                self.best_distance = this_best_distance
                self.best_trainer = this_best_trainer
            
            self.best_distances.append(this_best_distance)

            self.print_stats(generation_number, this_best_distance)

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
        """
        Provides a new list of trainers, based on the given generation.
        Performs crossover and mutations on the childs.
        Can also just copy some individuals (elite) into the next generation.
        """
        new_trainers = []

        if settings.ELITE_AMOUNT:
            new_trainers.extend(generation.get_elite(settings.ELITE_AMOUNT))

        if len(set([str(t.printable_path) for t in generation.trainers])) == 1:
            # This weird 'if' above will be True in case all the individuals are equal
            print('Population has converged. Finishing simulation.')
            exit()

        def get_parent_index():
            # Selects a parent (through the index),
            # based on the probability distribution.
            r = random()
            probs = generation.cumulative_probabilities
            for i in range(len(probs)):
                if probs[i] < r <= probs[i+1]:
                    return i
        
        # Runs until we have the correct amount of individuals for this generation
        while True:
            parent_1 = generation.ranked_trainers[get_parent_index()]
            parent_2 = generation.ranked_trainers[get_parent_index()]

            while parent_1.path == parent_2.path:
                # Parents are the same -- retry second parent
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
        """
        Order-1 type crossover operation.
        """
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
                    # This allel is already non-empty
                    continue
                child_chromosome[index] = next(
                    allel_b for allel_b in secondary_parent
                    if not allel_b in child_chromosome  # non-duplicates only
                )
            return child_chromosome

        return get_child_chromosome(chromosome_a, chromosome_b), get_child_chromosome(chromosome_b, chromosome_a)

    def mutate(self, chromosome):
        """
        Performs mutations on the chromosome based on the settings' probabilities.
        """
        def swap_allels(position1, position2):
            chromosome[position1], chromosome[position2] = chromosome[position2], chromosome[position1]
        
        r = random()
        if r <= settings.CHANCE_SHUFFLE_MUTATION:
            # Completely shuffles the chromosome
            shuffle(chromosome)
        
        elif r <= settings.CHANCE_SEQUENTIAL_SWAP_MUTATION:
            # Swaps a pair of subsequent allels
            base_index = randint(1, len(chromosome)-1)
            swap_allels(base_index-1, base_index)
        
        elif r <= settings.CHANCE_RANDOM_SWAP_MUTATION:
            # Swaps any pair of allels, not necessarily subsequent.
            # Can also sometimes just swap an allel for itself (i.e. do nothing)
            swap_allels(randint(0, len(chromosome)-1), randint(0, len(chromosome)-1))

    def print_stats(self, generation_number, this_best_distance):
        if generation_number == settings.NUM_GENERATIONS:
            print(f'\n\n--- END OF SIMULATION ---')
            print(f"Best trainer's distance: {'{0:.2f}m'.format(self.best_distance)}")
            print(f"Best trainer's path: {self.best_trainer.printable_path}")
        elif generation_number%(settings.NUM_GENERATIONS/100) == 0:
            print(f'\nGeneration number {generation_number}')
            print(f'Best across generations: {"{0:.2f}m".format(self.best_distance)}')
            print(f'Best of generation {generation_number}: {"{0:.2f}m".format(this_best_distance)}')
            print(f'List of distances: {["{0:.2f}m".format(t.distance) for t in self.generation.ranked_trainers]}')


if __name__ == '__main__':
    # Initializes a new neighborhood
    neighborhood = Neighborhood()

    # Prepares matplotlibs stuff
    fig = pyplot.figure()
    base_axes = fig.add_subplot(111)
    neighborhood.configure_plot(pyplot)

    # Displays the base map
    neighborhood.plot_map(base_axes)
    pyplot.show(block=False)
    input("Showing base map. Press [enter] to proceed.")

    # Adds all possible paths into the map
    neighborhood.plot_possibilities(base_axes)
    pyplot.show(block=False)
    input("Showing map possibilities. Press [enter] to proceed.")

    # Initializes a random generation
    generation = Generation(neighborhood=neighborhood)
    generation.setup_random_generation(settings.POPULATION_AMOUNT)
    
    # Prepares the simulation to be started
    sim = Simulation(neighborhood, generation)

    def animate(i):
        base_axes.clear()
        neighborhood.configure_plot(pyplot)
        neighborhood.plot_map(base_axes)
        try:
            sim.best_trainer.plot_path(base_axes)
        except AttributeError:
            pass
        base_axes.plot()
    
    # sim.run_simulation()
    
    # Spawns a new thread for executing the simulation,
    # enabling the program to dynamically plot the best individual.
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(sim.run_simulation)
        anim = animation.FuncAnimation(fig, animate, interval=500)
        pyplot.show()

    neighborhood.configure_plot(pyplot)
    sim.best_trainer.plot_path(base_axes)
