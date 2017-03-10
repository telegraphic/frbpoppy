from populate import generate
from dosurvey import observe
from plot import plot_pop
from log import pprint

# Generate FRB population
population = generate(1000)

# Observe FRB population
survey_population = observe(population, 'WHOLESKY')

# Plot populations

# Either with
#plot_pop(pops=[population, survey_population])

# Or with
#population.save()
#survey_population.save()
#plot_pop(files=['./data/results/population.csv', './data/results/population_pmsurv.csv'])