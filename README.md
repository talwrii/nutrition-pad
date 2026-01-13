# nutrition-pad
Nutrition display fo local network.

If you work from home then it may make sense to have dedicated tablets (which can be cheaply obtained - nexus 10 tablets are very cheap) for food entry with a limited number of items. In my experience tools like myfitnesspal become *very* annoying to use over time.

The other motivation is to separate recording from calorie display. In theory you want to know calories when making decision. But it is in practice advantageous to smear the food decision making out over the day.

This is designed to work with nexus 10's


## Usage
This needs a local network and a server that it can run. 
You can then run `nutrition-pad --host 0.0.0.0 --port 5000` and connect to it from one more more tablets.

I personally have three tablets to give me a number of of panes for recording food. And another tablet for display Updates are shared..


## Hacking / Testing
This is meant to work on old devices. I target the nexus 10 because these are cheap and readily available and have a large screen size. This assumes that emulate command can be run with andorid-emulate

