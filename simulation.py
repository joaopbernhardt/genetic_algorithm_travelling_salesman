import os
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Pipe
from random import randint, random, shuffle

from matplotlib import pyplot, animation

import settings
from individual import Individual, Generation
from world import World
from multiprocessing_utils import (
    get_last_message, get_pipes_messages, any_process_alive,
    validate_and_get_num_processes)


class Simulation:
    """
    Controller class for the simulation in general, that is,
    contains the loop which creates and evaluates generations,
    performs the crossovers, mutations.
    """
    def __init__(self, world, process_num=None):
        self.world = world
        self.generation = Generation(world, random=True)
        self.process_string = f"(Process {process_num})" if process_num else ""

        self.best_distances = []  # Best results for each generation

    def run_simulation(self, pipe_conn=None):
        print(f'--- STARTING SIMULATION {self.process_string}---')

        for generation_number in range(1, settings.NUM_GENERATIONS+1):
            # Creates a new generation based on the previous one
            self.generation = Generation(self.world, self.get_new_individuals(self.generation))

            # This generation's results
            this_best_individual = self.generation.get_best_individual()
            this_best_distance = this_best_individual.distance

            # Saves the result if it's the best one so far, across generations
            if generation_number == 1 or this_best_distance < self.best_distance:
                self.best_distance = this_best_distance
                self.best_individual = this_best_individual

            self.best_distances.append(this_best_distance)

            self.print_stats(generation_number, this_best_distance)

            if pipe_conn:
                if generation_number%(settings.NUM_GENERATIONS/200) == 0:
                    pipe_conn.send({
                        'best_distance': self.best_distance,
                        'best_individual_path': self.best_individual.path
                    })

                if generation_number == settings.NUM_GENERATIONS:
                    pipe_conn.close()

            # if self.has_converged():
                # break

    def run_multiprocess_simulation(self, num_processes):
        world = getattr(self, 'world', World())
        pipe_conns, processes = [], []

        for process_num in range(1, num_processes+1):
            # Prepares a new simulation in this world
            sim = Simulation(world, process_num)

            # Pipes for receiving the results
            parent_conn, child_conn = Pipe()
            pipe_conns.append(parent_conn)

            p = Process(
                target=sim.run_simulation,
                args=(child_conn,),
            )
            processes.append(p)
            p.start()

        # Grabs the pipes' messages while the processes are running,
        # saving the results into this Simulation object
        all_results = []
        while any_process_alive(processes):
            time.sleep(0.25)
            current_results = get_pipes_messages(pipe_conns)

            if not current_results:
                # No new messages
                continue

            this_best_distance = min([res['best_distance'] for res in current_results])
            this_best_individual_path = next(
                res['best_individual_path'] for res in current_results
                if res['best_distance'] == this_best_distance)

            all_results.append({
                'best_individual_path': this_best_individual_path,
                'best_distance': this_best_distance,
            })

            best_overall_distance = min([r['best_distance'] for r in all_results])
            best_overall_path = next(
                res['best_individual_path'] for res in all_results
                if res['best_distance'] == best_overall_distance)

            best_individual = Individual(self.world, path=best_overall_path)
            self.best_individual = best_individual


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

    def get_new_individuals(self, generation):
        """
        Provides a new list of individuals, based on the given generation.
        Performs crossover and mutations on the childs.
        Can also just copy some individuals (elite) into the next generation.
        """
        new_individuals = []

        if settings.ELITE_AMOUNT:
            new_individuals.extend(
                generation.get_elite(settings.ELITE_AMOUNT)
            )

        if len(set([str(t.printable_path) for t in generation.individuals])) == 1:
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
            parent_1 = generation.ranked_individuals[get_parent_index()]
            parent_2 = generation.ranked_individuals[get_parent_index()]

            while Individual.have_the_same_path(parent_1, parent_2):
                # Parents are the same -- retry second parent
                parent_2 = generation.ranked_individuals[get_parent_index()]

            child_a, child_b = Individual(self.world), Individual(self.world)

            child_a_path, child_b_path = self.crossover(parent_1, parent_2)
            self.mutate(child_a_path)
            self.mutate(child_b_path)
            child_a.path, child_b.path = child_a_path, child_b_path

            new_individuals.extend([child_a, child_b])
            if len(new_individuals) >= settings.POPULATION_AMOUNT:
                new_individuals = new_individuals[0:settings.POPULATION_AMOUNT+1]
                break

        return new_individuals

    @staticmethod
    def crossover(individual_a, individual_b):
        """
        Order-1 type crossover operation.
        """
        length = len(individual_a.path)

        chromosome_a = individual_a.path
        chromosome_b = individual_b.path

        random_slice = [randint(0, length), randint(0, length)]
        random_slice.sort()

        slice_negative = [
            index for index in range(settings.NUM_LOCATIONS)
            if index not in range(*random_slice)
        ]

        def get_child_chromosome(base_parent, secondary_parent):
            # TODO: this method is responsible for >50% of execution time
            # in a simulation. Find a way to improve performance.
            secondary_parent = tuple(secondary_parent)
            child_chromosome = [None] * settings.NUM_LOCATIONS
            child_chromosome[random_slice[0]:random_slice[1]] = base_parent[random_slice[0]:random_slice[1]]

            for index in slice_negative:
                child_chromosome[index] = next(
                    allel_b for allel_b in secondary_parent
                    if not allel_b in child_chromosome  # non-duplicates only
                )
            return child_chromosome

        # TODO: re-initialize random_slice?
        return get_child_chromosome(chromosome_a, chromosome_b), get_child_chromosome(chromosome_b, chromosome_a)

    @staticmethod
    def mutate(chromosome):
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
            print(f'\n\n--- END OF SIMULATION {self.process_string} ---')
            print(f"Best individual's distance: {'{0:.2f}m'.format(self.best_distance)}")
            print(f"Best individual's path: {self.best_individual.printable_path}")
        elif generation_number%(settings.NUM_GENERATIONS/100) == 0:
            print(f'\nGeneration number {generation_number} {self.process_string}')
            print(f'Best across generations: {"{0:.2f}m".format(self.best_distance)}')
            print(f'Best of generation {generation_number}: {"{0:.2f}m".format(this_best_distance)}')
            # print(f'List of distances: {["{0:.2f}m".format(t.distance) for t in self.generation.ranked_individuals]}')


def run_basic_simulation():
    # Initializes a new world
    world = World()

    sim = Simulation(world)
    sim.run_simulation()


def run_plotted_simulation(num_processes="max"):
    num_processes = validate_and_get_num_processes(num_processes)

    # Initializes a new world
    world = World()

    # Prepares matplotlibs stuff
    fig = pyplot.figure()
    base_axes = fig.add_subplot(111)
    world.configure_plot(pyplot)

    # Displays the base map
    world.plot_map(base_axes)
    pyplot.show(block=False)
    input("Showing base map. Press [enter] to proceed.")

    # Adds all possible paths into the map
    world.plot_possibilities(base_axes)
    pyplot.show(block=False)
    input("Showing map possibilities. Press [enter] to proceed.")

    # Initializes a random generation
    generation = Generation(world=world)
    generation.setup_random_generation(settings.POPULATION_AMOUNT)

    # Prepares the simulation to be started
    sim = Simulation(world)

    def animate(i):
        base_axes.clear()
        world.configure_plot(pyplot, gen=len(sim.best_distances))
        world.plot_map(base_axes)
        try:
            sim.best_individual.plot_path(base_axes)
        except AttributeError:
            pass
        base_axes.plot()

    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=4, metadata=dict(artist='João Paulo Bernhardt'), bitrate=1800)

    # Spawns a new thread for executing the simulation,
    # enabling the program to dynamically plot the best individual.
    with ThreadPoolExecutor(max_workers=1) as executor:
        if num_processes > 1:
            executor.submit(sim.run_multiprocess_simulation, num_processes)
        else:
            executor.submit(sim.run_simulation)

        anim = animation.FuncAnimation(fig, animate, interval=250)

        # Uncomment this to save the animation
        # anim.save(f'tsp_{settings.NUM_LOCATIONS}_locations.mp4', writer=writer)
        pyplot.show()

    world.configure_plot(pyplot)
    sim.best_individual.plot_path(base_axes)


if __name__ == '__main__':
    run_plotted_simulation()
