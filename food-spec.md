# Food Spec

Foods live in `foods.toml` under `[pads.<pad_name>.foods.<food_key>]`.

## Fields

**Required:**
- `name` - Display name
- `type` - Either `"amount"` (per gram) or `"unit"` (fixed portion)

**Optional (all types):**
- `display_name` - Short name shown on buttons and saved to logs. Falls back to `name` if not set.
- `active` - Set to `false` to hide from the button grid. Defaults to `true`. Inactive foods still work for historical log entries.

**For `type = "amount"`:**
- `calories_per_gram`
- `protein_per_gram`
- `fat_per_gram` (optional)
- `saturated_fat_per_gram` (optional)
- `carbs_per_gram` (optional)
- `fiber_per_gram` (optional)
- `sugar_per_gram` (optional)
- `salt_per_gram` (optional)

**For `type = "unit"`:**
- `calories`
- `protein`
- `fat` (optional)
- `saturated_fat` (optional)
- `carbs` (optional)
- `fiber` (optional)
- `sugar` (optional)
- `salt` (optional)

## Example
```toml
[pads.vegetables.foods.avocado]
name = "Avocado"
type = "amount"
calories_per_gram = 1.60
protein_per_gram = 0.02
fat_per_gram = 0.15
saturated_fat_per_gram = 0.021
carbs_per_gram = 0.085
fiber_per_gram = 0.067
sugar_per_gram = 0.007

[pads.proteins.foods.eggs]
name = "Eggs (2 large)"
type = "unit"
calories = 140
protein = 12
fat = 10
saturated_fat = 3
carbs = 1
fiber = 0
```