# Architecture

## Problems

The entire architecture for this application is very heavily bound by the following imposed limits.
The following issues are resolved or have some solutions/partial solutions:

* API requests from the entire application are limited to approximately 2 requests per second
* Large amounts of data change live out of sync
* Large amounts of data do *NOT* change and are mainly static during a game period
* Data gets reset on a reserved interval (viewable at `/status` under `.server_resets.next`.)
* Different ships really are capable of different activities and serve different purposes entirely
* Ships and actions in general take a long time to do (often >30s, and so each ship's actions can wait
for the preceding operation to complete)
* There is some occasional brittleness on the backend (and live data changes) as this is still beta. This means
previously cached data may no longer applicable because of fundamental holistic changes mid-game period.
* The bulk of the data is heavily unstructured, as in we must determine routes based on constraints (ex: a ship
may be unable to operate at `CRUISE` speed from start location to end, and will need to find the optimum path
along its route. Not all nodes in a system have markets that sell fuel, so we will have to find a route that specifically
has fuel for sale).

Unresolved issues:

* The meta for the game itself changes every game period (Unresolved)

## Solutions

As a consequence, the following solutions were implemented for each of the above constraints outlined below.

### Caches and Persistence

Issues resolved: 

> Large amounts of data do *NOT* change and are mainly static during a game period

There's a few different persistence layers that all go through the DAO (SQLModel/SQLAlchemy-based long-term persistence via SQLite)

* Data that can't easily be retrieved without huge latency. Ex: Must travel to market (minutes/hours) to collect market data,
so we cache it in the data layer. These models aren't 1:1 necessarily with the backend and storing only what fields are used 
in application code is prioritized.
* Internal operations and structure. Ex: storing data in queues into persistence to adjust logical behavior of different classed
fleet members. (Ex: a trader has its upcoming tasks stored in the db, and will execute them in order)
* Client responses. Instead of using the 2 RPS limit, some requests and responses are cached with a TTL (ex: waypoint list).

`Cache` - from `trader.client.request_cache` - A singleton class that acts as a request cache
`DAO` - from `trader.dao.dao` - A singleton class that acts as a datastore for anything needing persistence and caching

### Cache Bypasses and Resets

Issues resolved: 

> Data gets reset on a reserved interval (viewable at `/status` under `.server_resets.next`.)

> Large amounts of data change live out of sync

### Logic and Roles

Issues resolved: 

> Ships and actions in general take a long time to do (often >30s, and so each ship's actions can wait
> for the preceding operation to complete)



### Graphs

Issues resolved: 

> The bulk of the data is heavily unstructured, as in we must determine routes based on constraints

The bulk of data is geographic in nature (x, y) with additional data. Using `networkx` for the graph construction
and being able to connect different resources together.

### Queues

Issues resolved: 

> API requests from the entire application are limited to approximately 2 requests per second

> Ships and actions in general take a long time to do (often >30s, and so each ship's actions can wait
for the preceding operation to complete)

Queues. Lots of queues. Each ship operates on a queue. Every request is bound through a singular request queue
which is throttled to approximately 1.5 RPS (`MAXIMUM_REQUESTS_PER_SECOND`). The bulk of the queues can be found
in `trader.queues` module and package. The types of queues:

* __BaseQueue__ - all queues use this via inheritance
* __ActionQueue__ - used for actioned events (for example, each logic class has a queue). As this is governed by 
a queue, it is also easier to stop what a logic class is doing and tell it to do something else (without waiting
for it to complete). This acts as a very very primitive DAG.
* __RequestQueue__ - used for all client requests (to throttle requests for the entire application). Has primitive 
retry logic and error logging.

## Constraints

This application is intended to run off a single machine for the time being, so if distributed work is desired, 
a number of classes will need to store their class state in a remote data store AND to avoid bypassing the queues,
a mutex/lock is probably desired per BaseQueue class to avoid.
