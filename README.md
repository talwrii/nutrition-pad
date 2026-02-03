# nutrition-pad
Nutrition display for local network.

## Philosophy

Track your macros, they say. Calories in calories out. It's easy... until you do it **every day, while juggling other goals**. nutrition-pad is designed to make logging and decision making easier. nutrition-pad is an opinionated approach for technologically familiar people who work from home and are willing to buy (cheap) hardware.

Recording what you eat and altering your eating behaviour based on information derived from these logs — such as macronutrient targets — is something that many people do — sometimes successfully. But each decision and each log comes with a little cost (and perhaps an internal goal-related reward). Most calorie tracking apps seem oddly unoptimised for expert habitual entry — there is friction in both recording and checking. We want to make the decision easier by smearing it out over the day where possible, separating recording from display.

The "trick" for making recording easier is using a *lot* of tablets — so mostly useful for a work-from-home setting, as well as creating your own menu of commonly used items. The trick for decision making is displaying this information in many places.

More tablets! The idea is that you have a dedicated tablet for each piece of functionality — or maybe a pair of things that you can toggle between. I also have tablets around my house for displaying numbers. If you work from home then it may make sense to have dedicated tablets (which can be cheaply obtained - nexus 10 tablets are very cheap) for food entry with a limited number of items. In my experience tools like myfitnesspal become *very* annoying to use over time.

The other motivation is to separate recording from calorie display. In theory you want to know calories when making a decision. But it is in practice advantageous to smear the food decision making out over the day.

Designed for the Nexus 10, as this is a cheap large-screened tablet. I also use Nexus 7s and 9s (since they are available).

## More tablets, you say?

So what exactly do I mean by more tablets? Well... I at the moment use about 10 tablets. But thankfully tablets have now got *very* cheap. I have four tablets which display foods so I can click on them in one go, one tablet for setting the amounts of food, and then various other tablets around my house to display nutrition statistics and logs.

# Features

* Use multiple tablets so that you can remember food positions and don't have to use your phone
* Separate display and entry to avoid decision fatigue with decision smearing
* 


## Usage
This needs a local network and a server that it can run. 
You can then run `nutrition-pad --host 0.0.0.0 --port 5000` and connect to it from one or more tablets.

I personally have three tablets to give me a number of panes for recording food. And another tablet for display. Updates are shared.

## Hacking / Testing
This is meant to work on old devices. I target the nexus 10 because these are cheap and readily available and have a large screen size. This assumes that emulate command can be run with android-emulate


## LLM usage
This is good for LLM usage. An LLM can help you. See [[LLM use]]

