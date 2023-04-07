import sqlite3
import pandas as pd
from datetime import date
import numpy as np
import matplotlib.pyplot as plt
import mplcursors

db = "data/newdb.db"

# STATS WINDOWS Important - would add to complexity due to aggregate functions,
# try to get this working asap
# IDEAS:
# statistics by deck and whole collection
# -TODAY no of cards studied, total time spent studying, avg time, counts for each difficulty and %
# correct answers on mature cards (i.e. hard, good or easy on cards with previous intervals of > 21/30 days)
# GENERAL
# cards due in the future, plot by days ahead and no
# [work out way to show historic reviews (number on each day)] - matplotlib imshow(z)?
# ^ breakdown of these past reviews on whether cards were young, mature, learning, relearning, new etc.
# [both time spent and no of reviews] ^
# Pie chart breakdown of cards in the deck
# Plot of card intervals
# bar chart of card ease factors
# Success rate breakdown by hours over a given time frame
# Answer buttons pressed for each card type - (re+)learning, young, mature
# When cards were added? Not sure how this would be done or if it serves mutch purpose
# also want session statistics maybe?
# be open to any other ideas or suggestions


con = sqlite3.connect(db)
cur = con.cursor()
cur.execute(f"""SELECT r.ucid, r.ease, r.ivl, r.lastivl, r.ef, r.lastef,
 r.status, r.reps, r.lapses, r.time, r.start, r.end
 FROM revlog r INNER JOIN user_cards uc ON r.ucid = uc.id WHERE uc.uid = ?""", (2,))
revsdf = pd.DataFrame(cur.fetchall(),
                  columns=['ucid', 'ease', 'ivl', 'lastivl', 'ef', 'lastef',
                           'status', 'reps', 'lapses', 'time', 'start', 'end'])
print(revsdf)

cur.execute(f"""SELECT cid, ef, ivl, type, status, reps, lapses, due FROM user_cards WHERE uid = ?""", (2,))

cardsdf = pd.DataFrame(cur.fetchall(), columns=['cid', 'ef', 'ivl', 'type', 'status', 'reps', 'lapses', 'due'])
cardsdf['due'] = pd.to_datetime(cardsdf['due'], unit='s', origin='unix')
cardsdf['due'] = cardsdf['due'].dt.date # Rounds down due times to the nearest date
cardsdf['due'] = (cardsdf['due'] - date.today()).dt.days
due_counts = cardsdf.groupby(['due']).size().reset_index(name='count')

print(cardsdf)
print(cardsdf[['cid', 'due']])
print(due_counts)

# fig, ax = plt.subplots()
# ax.bar(due_counts['due'], due_counts['count'])
# ax.set_xlabel('Due Date')
# ax.get_yaxis().set_visible(False)
# # ax.set_ylabel('Number of Cards Due')
# # ax.set_title('Number of Cards Due in the Future')
# plt.show()

fig, ax = plt.subplots()
barplot = ax.bar(due_counts['due'], due_counts['count'], zorder=1, color='#007CBE')
ax.set_xlabel('Due Date')

# ax.get_yaxis().set_visible(False)
ax2 = plt.twinx()
plt.xlim([min(0, min(due_counts['due'])), 30 + 0.5])
ax2.plot(due_counts['due'], due_counts['count'].cumsum(), c='grey')  # work out ways to display this better
ax2.fill_between(due_counts['due'], 0, due_counts['count'].cumsum(), alpha=0.1, color='grey')
plt.ylim(0, max(due_counts['count'].cumsum()) + 0.5)

# ax.set_zorder()
# ax2.set_zorder(1)


# ax.set_xlim(left=min(0, min(due_counts['due'])))
# barplot.xlim([min(0, min(due_counts['due'])), max(due_counts['due'])])


# Define the content of the tooltip
tooltip_fmt = "In {} Days\nCards Due: {}\n Running Total: {}"
print(due_counts['count'].cumsum())
print(*zip(due_counts['due'], due_counts['count']), due_counts['count'].cumsum())
tooltip_text = [tooltip_fmt.format(d, c, b) for d, c, b in
                (zip(due_counts['due'], due_counts['count'], due_counts['count'].cumsum()))]


# Add a cursor to the bar plot
c1 = mplcursors.cursor(barplot, hover=True)
c1.connect("add", lambda sel: sel.annotation.set_text(tooltip_text[sel.index]))


@c1.connect("add")
def _(sel):
    sel.annotation.get_bbox_patch().set(fc="white")
    sel.annotation.arrow_patch.set(arrowstyle="simple", fc="white", alpha=.5)


plt.show()

# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
# import datetime
# import numpy as np
#
# # Generate some dummy data
# dates = [datetime.datetime(2022, 1, 1) + datetime.timedelta(days=i) for i in range(50)]
# counts = np.random.randint(1, 10, size=(50, 7))
#
# # Convert the dates to a format that can be plotted using imshow()
# x = np.arange(len(dates))
# y = np.arange(7)
# xx, yy = np.meshgrid(x, y)
# values = counts.T
#
# # Create a figure and axes object
# fig, ax = plt.subplots()
#
# # Plot the data using imshow()
# im = ax.imshow(values, cmap='YlOrRd', vmin=0, vmax=10)
#
# # Set the X-axis format to display dates
# date_format = mdates.DateFormatter('%Y-%m-%d')
# ax.xaxis.set_major_formatter(date_format)
# ax.set_xticks(np.arange(len(dates)))
# ax.set_xticklabels(dates)
# fig.autofmt_xdate()
#
# # Add axis labels and a title
# ax.set_xlabel('Date')
# ax.set_ylabel('Weekday')
# ax.set_title('Review Heatmap')
#
# # Add a colorbar
# cbar = ax.figure.colorbar(im, ax=ax)
# cbar.ax.set_ylabel("Review Count", rotation=-90, va="bottom")
#
# # Set the tick labels and tick positions for the x-axis and y-axis
# ax.set_xticks(x)
# ax.set_xticklabels(dates, rotation=45, ha='right')
# ax.set_yticks(y)
# ax.set_yticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
#
# # Adjust the size and spacing of the squares
# ax.set_aspect('equal', 'box')
# ax.set_xlim(-0.5, len(dates)-0.5)
# ax.set_ylim(-0.5, 6.5)
# ax.invert_yaxis()
#
# # Show the plot
# plt.show()
