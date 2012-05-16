veezio API
==========

This is the veezio public API.


Endpoints
=========

Search
------

GET /search

Query string:
- q: query
- start:
- max-results:

Channel endpoint
----------------

Create channels
~~~~~~~~~~~~~~~

POST /channels

Update channel
~~~~~~~~~~~~~~

PUT /channels.:format

List channels
~~~~~~~~~~~~~

GET /channels.:format

Get info
~~~~~~~~

GET /channels/:id.:format

Get channel's videos
~~~~~~~~~~~~~~~~~~~~

GET /channels/:id/videos.:format

Process new video in a channel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

POST /channels/:id/videos

Query string:
- start: beginning (in seconds)
- length: length of the video to process (in seconds)
- lang: language of the video (eng, fre)

Video endpoint
--------------

Get all videos
~~~~~~~~~~~~~~

GET /videos.:format

Get info
~~~~~~~~

GET /videos/:id.:format
GET /videos/:id/transcript.:format
GET /videos/:id/concepts.:format
GET /videos/:id/keywords.:format

Delete a video
~~~~~~~~~~~~~~

DELETE /videos/:id


SEO
---

GET /videos/:id/seo.:format

API versioning
==============

Latest:
http://api.veez.io/v3/channels/...
http://api.veez.io/v2/channels/...

Pagination
==========

limit & offset

Limiting output
===============

/channels/:id.:format?fields=id,title

Error handling
==============

HTTP codes

Available output formats
========================

JSON
