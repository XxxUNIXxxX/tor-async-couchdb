# Basic Sample
This service implements a simple RESTful service that
demonstrates how the basic features of ```tor-async-couchdb``` were intended to be used.
This is the first in a series of samples services.
We'll build on this basic sample service as we explore the more
advanced features of ```tor-async-couchdb```.

This sample is a 2-tier application - an app tier talking to a data tier.
The app tier is a service that exposes a RESTful API
which allows the creation, retrieval, update and delete of fruit resources.
The application tier is implemented using using
Tornado's [Asynchronous and non-Blocking I/O](http://tornado.readthedocs.org/en/latest/guide/async.html)
and ```tor-async-couchdb```.
The data tier is implemented using CouchDB.

# Creating the CouchDB Database

See [db_installer](../db_installer) which describes how to create the CouchDB
Database that the sample service will use.

# Running the Service

## Command line options
```bash
>./service.py --help
Usage: service.py [options]

This service implements a simple RESTful service that demonstrates how tor-
async-couchdb was intended to be used.

Options:
  -h, --help           show this help message and exit
  --port=PORT          port - default = 8445
  --ip=IP              ip - default = 127.0.0.1
  --database=DATABASE  database - default =
                       http://127.0.0.1:5984/tor_async_couchdb_sample_basic
```

## Startup
```bash
>./service.py
2015-04-22T11:56:57.724+00:00 INFO service service started and listening on http://127.0.0.1:8445 talking to database http://127.0.0.1:5984/tor_async_couchdb_sample_basic
```

# Is the Service Working?

## Integration Tests
Once you have spun up the sample services you can run
a sanity test suite against the service using a
[nose](https://nose.readthedocs.org/en/latest/) runnable
integration test suite in [tests.py](../tests.py).
The test suite is hard-coded to talk to a service at
[http://127.0.0.1:8445](http://127.0.0.1:8445) so edit
the test if you are running the service at a different
endpoint.

```bash
>nosetests tests.py
...
----------------------------------------------------------------------
Ran 3 tests in 0.646s

OK
>
```

## Stress Tests
Another way to verify the service is working correctly is to stress
the service by driving lots of concurrent requests into the service
and observing that all requests are successfully serviced.
The [loadgen](../loadgen) utility can be used to generate lots of
concurrent requests.

>This basic service will successful service lots of concurrent
>```POST``` and ```GET``` requests so you'll want to ensure that
>[loadgen](../loadgen) only issues lots of these kinds of requests.
>As we build on this basic sample service we'll enhance
>the basic service to successfully deal with lots of concurrent
>```PUT``` and ```DELETE``` requests.

# Exercising the Service's API

## Create
```bash
>curl -s -X POST http://127.0.0.1:8445/v1.0/fruits | python -m json.tool
{
    "_id": "345d17dae686f2b435881085198afc39",
    "_rev": "1-9e08c14213bb8b4386eea863de966d9e",
    "created_on": "2015-04-22T11:58:41.347308+00:00",
    "fruit": "fig",
    "fruit_id": "455aab1b747e40a89034877e2c963179",
    "updated_on": "2015-04-22T11:58:41.347308+00:00"
}
>
```

## Read
```bash
>curl -s http://127.0.0.1:8445/v1.0/fruits/455aab1b747e40a89034877e2c963179 | python -m json.tool
{
    "_id": "345d17dae686f2b435881085198afc39",
    "_rev": "1-9e08c14213bb8b4386eea863de966d9e",
    "created_on": "2015-04-22T11:58:41.347308+00:00",
    "fruit": "fig",
    "fruit_id": "455aab1b747e40a89034877e2c963179",
    "updated_on": "2015-04-22T11:58:41.347308+00:00"
}
>
```

## Update
```bash
>curl -s -X PUT http://127.0.0.1:8445/v1.0/fruits/455aab1b747e40a89034877e2c963179 | python -m json.tool
{
    "_id": "345d17dae686f2b435881085198afc39",
    "_rev": "2-233923144d85b62e26c13013e9d30eeb",
    "created_on": "2015-04-22T11:58:41.347308+00:00",
    "fruit": "kiwi",
    "fruit_id": "455aab1b747e40a89034877e2c963179",
    "updated_on": "2015-04-22T11:58:41.347308+00:00"
}
>curl -s -X PUT http://127.0.0.1:8445/v1.0/fruits/455aab1b747e40a89034877e2c963179 | python -m json.tool
{
    "_id": "345d17dae686f2b435881085198afc39",
    "_rev": "3-fe7b3d270fa598b88d646687488aa766",
    "created_on": "2015-04-22T11:58:41.347308+00:00",
    "fruit": "orange",
    "fruit_id": "455aab1b747e40a89034877e2c963179",
    "updated_on": "2015-04-22T11:58:41.347308+00:00"
}
>
```

## Delete
```bash
>curl -s  -o /dev/null -w "%{http_code}\n" -X DELETE http://127.0.0.1:8445/v1.0/fruits/455aab1b747e40a89034877e2c963179
200
>curl -s  -o /dev/null -w "%{http_code}\n" -X DELETE http://127.0.0.1:8445/v1.0/fruits/455aab1b747e40a89034877e2c963179
404
>
```

## Read All
```bash
>#create 10 fruit resources
>for i in `seq 10`; do curl -s -X POST http://127.0.0.1:8445/v1.0/fruits; done
>#lots of output cut
>curl -s http://127.0.0.1:8445/v1.0/fruits | python -m json.tool
>#lots of output cut
```

# Service's Data Model
```bash
curl http://127.0.0.1:5984/tor_async_couchdb_sample/_design/fruit_by_fruit_id/_view/fruit_by_fruit_id?include_docs=true
```
