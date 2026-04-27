# Catalog Engine Regression Check

## Result

- Bullet core equal: `True`
- Powder core equal: `True`
- Powder model core equal: `True`
- Bullet core delta: `0`
- Powder core delta: `0`
- Powder model core delta: `0`

## Import Counts

- Raw bullets: `5824` | Clean bullets: `5824`
- Raw powders: `258` | Clean powders: `258`
- Raw lots: `906` | Clean lots: `906`
- Raw powder models: `258` | Clean powder models: `258`
- Raw usable powder models: `256` | Clean usable powder models: `256`

## Interpretation

- This check imports raw and cleaned catalogs into separate temporary databases.
- It then compares engine-critical fields in `bullets`, `powder`, and `powder_database`.
- Matching core sets mean the cleanup pass changed naming/presentation consistency only, not the motor-relevant seed data.
