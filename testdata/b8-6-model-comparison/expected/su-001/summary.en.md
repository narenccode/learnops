<!-- PROVISIONAL, NOT REVIEWED: author-drafted expected output for B8.6 item su-001. Not checked by a mentor. -->
A cache keeps a copy of recently used data close to a program, so repeated requests do not wait
for a slow disk or network. Caches work because programs show locality: they reuse the same data
soon (temporal locality) and use data stored next to it (spatial locality). When the cache is full,
an eviction policy decides what to remove. Least recently used (LRU) is the most common; first in,
first out is simpler but can remove data still in use. Cached copies go stale when the original
changes, so they need a time to live or invalidation on write. This week's exercise: add a small
LRU cache to your assistant and measure how many answers it serves from the cache.
