# llm-use

## Fixing unknoowns
Run nutrition-notes to get unknowns. We want none in the last couple of days.

You can work out what the unknown is from adjacent notes. Use the internet to get values. We want recent values.

## Updating notes
A commaond problem is not having entries for the foods you create.
You can `nutrition-notes` to get information for this

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
