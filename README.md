# Drawio to limesurvey

Scripts for conversion of DADESS survey graphs to limesurvey input csvs

## Execute
Install the python modules

```
virtualenv --python=python3 venv
source venv/bin/activate
pip install -r requirements.txt
```

Launch the test
```
python process_graph.py --files_list branch1.xml branch2.xml  --names_list name1 name2
```
