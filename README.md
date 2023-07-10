# 17LandsMetaTracker
Using 17 lands color_ratings data plot percentage of games played by colour by date.

As of Jul 9th - this is a work in progress.

INSTALLATION:
See requirements.txt for required packages.  I would recommend setting up a
virtual environment, clone the repo, and then run:
>pip install -r requirements.txt

EXECUTION:
This is a python command line application currently - run it in a
shell per:
>python meta_game_analysis.py

It will prompt you for which set, format, and user tier you would like
to analyze.

DESCRIPTION:
Using data from https://www.17lands.com/color_ratings, 
track daily number of games played per color combination.  Data is 
cached locally to avoid hammering the site repeatedly, so only
new or previously unread data is fetched.

Plot a selection of color combinations as a percentage of overall games.  
The resulting graph shows the changes in what players are drafting daily.  
Allowing the user to see what decks are currently heavily or under drafted. 
The direction of the slope of each line provides some indication of 
whether the deck is decreasing or increasing in popularity.
