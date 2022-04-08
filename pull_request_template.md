# Description and related issues

Please include a summary of the changes and any issues which are addressed.

Closes #(issue number)

# Checklist:

- [ ] All tests pass or xfail on catscan: run `pytest --basetemp=tmp -sv -n 8 tests` on catscan from the root directory
- [ ] Docs build with no errors: run `make clean & make html` from the `docs` folder
- [ ] No python formatting errors: run `flake8 nsds_lab_to_nwb tests` from the root directory
- [ ] If needed, docs have been update: `docs/source` has been updated for any added, moved, or removed files
