# from PyQt5.QtGui import QStandardItemModel
# from PyQt5.QtWidgets import QTreeView, QComboBox
# from PyQt5.QtCore import QItemSelection
# import datetime
# from time import time
#
# i = QItemSelection()
# combobox = QComboBox()
#
# model = QStandardItemModel()
# model.item
#
# tree = QTreeView
# tree.header().setSectionsMovable(False)
#
# today = datetime.date.today()
# timestamp = int(time.mktime(today.timetuple()))

# # TODO USE THIS FOR PLOTTING ANSWERS BAR CHART

import matplotlib.pyplot as plt

# Define the data for the bar chart
categories = ['Category A', 'Category B', 'Category C']
values1 = [10, 15, 20]
values2 = [5, 10, 15]

# Set the width of each bar
bar_width = 0.35

# Calculate the x-axis positions for each group of bars
x_pos = [i for i in range(len(categories))]

# Create the figure and axis objects
fig, ax = plt.subplots()

# Plot the bars for the first set of values
ax.bar(x_pos, values1, width=bar_width, color='b', label='Values 1')

# Plot the bars for the second set of values
ax.bar([i + bar_width for i in x_pos], values2, width=bar_width, color='g', label='Values 2')

# Set the x-axis tick positions and labels
ax.set_xticks([i + bar_width / 2 for i in x_pos])
ax.set_xticklabels(categories)

# Set the axis labels and title
ax.set_xlabel('Category')
ax.set_ylabel('Value')
ax.set_title('Bar Chart with Multiple Categories')

# Add a legend
ax.legend()

# Show the plot
plt.show()


# import matplotlib.pyplot as plt
#
# # Define the data for the bar chart
# categories = ['Category A', 'Category B', 'Category C']
# values1 = [10, 15, 20]
# values2 = [5, 10, 15]
#
# # Set the width of each bar
# bar_width = 0.8
#
# # Calculate the x-axis positions for each group of bars
# x_pos = [i for i in range(len(categories))]
#
# # Calculate the y-axis positions for the bars
# y_pos = [values1[i] + values2[i] for i in range(len(categories))]
#
# # Create the figure and axis objects
# fig, ax = plt.subplots()
#
# # Plot the bars for each pair of values
# ax.bar(x_pos, values1, width=bar_width, color='b', label='Values 1')
# ax.bar(x_pos, values2, bottom=values1, width=bar_width, color='g', label='Values 2')
#
# # Set the x-axis tick positions and labels to show pairs of categories
# ax.set_xticks([i for i in range(len(categories))])
# ax.set_xticklabels([f'{categories[i]}-{categories[i+1]}' for i in range(0, len(categories), 2)])
#
# # # Set the x-axis tick positions and labels
# # ax.set_xticks([i + bar_width / 2 for i in x_pos])
# # ax.set_xticklabels(categories)
#
# # Set the axis labels and title
# ax.set_xlabel('Category Pairs')
# ax.set_ylabel('Value')
# ax.set_title('Bar Chart with Pairs of Categories')
#
# # Add a legend
# ax.legend()
#
# # Show the plot
# plt.show()

# import matplotlib.pyplot as plt
#
# # Define the data for the bar chart
# categories = ['Category A', 'Category B', 'Category C', 'Category D', 'Category E', 'Category F']
# values1 = [10, 15, 20, 25, 30, 35]
# values2 = [5, 10, 15, 20, 25, 30]
#
# # Set the width of each bar
# bar_width = 0.5
#
# # Calculate the x-axis positions for each pair of bars
# x_pos = [i for i in range(len(categories))]
#
# # Create the figure and axis objects
# fig, ax = plt.subplots()
#
# # Plot the bars for each pair of values
# ax.bar(x_pos, values1, width=bar_width, color='b', label='Values 1')
# ax.bar(x_pos, values2, width=bar_width, color='g', bottom=values1, label='Values 2')
#
# # Set the x-axis tick positions and labels to show pairs of categories
# tick_positions = []
# tick_labels = []
# for i in range(0, len(categories), 2):
#     if i == len(categories) - 1:
#         # Handle case where there is an odd number of categories
#         tick_positions.append(i)
#         tick_labels.append(categories[i])
#     else:
#         tick_positions.append(i + 0.5)
#         tick_labels.append(f'{categories[i]} {categories[i+1]}')
# ax.set_xticks(tick_positions)
# ax.set_xticklabels(tick_labels)
#
# # Set the axis labels and title
# ax.set_xlabel('Category Pairs')
# ax.set_ylabel('Value')
# ax.set_title('Stacked Bar Chart with Pairs of Categories')
#
# # Add a legend
# ax.legend()
#
# # Show the plot
# plt.show()

""""""
# import datetime
# from time import mktime
#
# daysrange = 30
# today = datetime.date.today()
# todaytimestamp = int(mktime(today.timetuple()))
# daystarts = [todaytimestamp]
# days_x = [0]
# for i in range(daysrange):
#     daystart = todaytimestamp - (i + 1) * 86400
#     daystarts.append(daystart)
#     days_x.append(-(i+1))
# daystarts.reverse()
# days_x.reverse()
# print(daystarts)
# print(days_x)


# import matplotlib.pyplot as plt
#
# # Define the data for the bar chart
# categories = ['Category A', 'Category B', 'Category C']
# values1 = [10, 15, 20]
# values2 = [5, 10, 15]
#
# # Set the width of each bar
# bar_width = 0.5
#
# # Calculate the x-axis positions for each pair of bars
# x_pos = [i for i in range(len(categories))]
#
# # Create the figure and axis objects
# fig, ax = plt.subplots()
#
# # Plot the bars for each pair of values
# ax.bar(x_pos, values1, width=bar_width, color='b', label='Values 1')
# ax.bar(x_pos, values2, width=bar_width, color='g', bottom=values1, label='Values 2')
# # sum the bottom of the previous values for further...
#
# # Set the x-axis tick positions and labels to show the categories
# ax.set_xticks(x_pos)
# ax.set_xticklabels(categories)
#
# # Set the axis labels and title
# ax.set_xlabel('Categories')
# ax.set_ylabel('Value')
# ax.set_title('Stacked Bar Chart with Paired Values')
#
# # Add a legend
# ax.legend()
#
# # Show the plot
# plt.show()








