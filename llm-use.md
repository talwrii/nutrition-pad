# llm-use

## Adding Foods
```nutrition-food add << 'EOF'
[pads.PADNAME.foods.food-key]
name = "Human Readable Name"
type = "amount"  # or "unit"
calories_per_gram = 1.26
protein_per_gram = 0.289
EOF
```

For type = "unit" foods, use calories and protein instead of the _per_gram variants.
