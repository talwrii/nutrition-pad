# llm-use

## Fixing unknoowns
A common part of tracking food is not having an existing entry in the food database for a food. Having to immediately create an entry while calorie tracking can contribute to fatigue, or simply be impossible. We provide a system to delay the entry of a food with so-called "unknowns". This lets us create an entry that we file in later along with notes about the food.

You can run `nutrition-notes` to get the entries with an unknown food. Nearby notes inform you about what the entry probably is.  We want to have no unknown entries for the last couple of days.
You can use the internet to get nutrition inforation about a food. Prefer more recent entries. Try to find two sources that match. Prefer direct entries from menus.


Once you create the food fo the unknown or otherwise find the food, you can use `nutrition-unkonwn` to add a food to an unknown entry.

## Updating notes
A commaond problem is not having entries for the foods you create.
You can `nutrition-notes` to get information for this

## Changed foods
Soetimes you can make errors when creating food. You should just change these immediately.
If there is a change you show make the food as inactive and create a new entry going forward.

## Adding Foods
Always use `nutrition-food add` to add foods rather than editing foods.toml directly.

```nutrition-food add << 'EOF'
[pads.PADNAME.foods.food-key]
name = "Human Readable Name"
type = "amount"  # or "unit"
calories_per_gram = 1.26
protein_per_gram = 0.289
EOF
```

For type = "unit" foods, use calories and protein instead of the _per_gram variants.
