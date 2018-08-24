This example uses the [luigi](https://luigi.readthedocs.io/en/stable/) framework.

## How to use:

- Install requirements in a virtualenv
```
python3 -m virtualenv myvenv
source myvenv/bin/activate
pip install -r requirements.txt
```

- Start databases with docker-compose:

``` bash
docker-compose up -d
```

- In a shell start a luigi daemon scheduler from the directory which contains `log.cfg` and `luigi.cfg`

``` bash
luigid
```


- Execute any tasks defined in the module `tasks.tasks`:

``` bash
PYTHONPATH=. luigi --module tasks.tasks <Task> [<parameters>,...]
```

For example to launch the whole process from download videos to insert in mongo:

``` bash
PYTHONPATH=. luigi --module tasks.tasks SaveAllVideoInMongo --workers 3
```

**You can specify the number of workers running in parallele (3 should be enough for small computer's configurations)**

## Monitoring

open *http://localhost:8082*

to see the history of tasks:

open *http://localhost:8082/history*


