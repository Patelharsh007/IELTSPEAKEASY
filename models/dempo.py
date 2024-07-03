import random

# Example list of categories
categories = ['Science', 'Math', 'History', 'Geography', 'Art']

# Number of categories to randomly select
count = 2

# Randomly select 'count' categories from the list
selected_categories = random.sample(categories, count)

print(selected_categories)