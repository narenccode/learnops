I built a small assistant that answers one kind of question: how many days are left until a
date the user types. I chose it because the answer can be checked exactly, so I always knew when
it was wrong.

What worked: the date parsing was easier than I expected. Python's standard library reads dates
in the year-month-day form, and I wrote tests for the first and last day of a month, a leap day,
and a date in the past. All of them pass. Publishing the demo also went well once I understood
that the page must answer quickly, so I kept the code very small.

What did not work: my first version tried to understand dates written in words, like "next
Friday". It guessed wrong often enough that I removed it. I also lost an afternoon to a clock set
to another time zone.
