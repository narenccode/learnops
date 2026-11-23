This week my helper started answering questions from a document, the Zephyr Lane Tool Library
handbook. It breaks the handbook into paragraphs and gives back the paragraph with the most words
in common with the question. I checked it with ten questions written before I ran it.

Two questions it handles badly:

1. "Can I take a sander home for two weeks?" It gives the borrowing paragraph, which says seven
days, but it never answers "no". The helper only returns text and cannot compare two weeks with
seven days, so the reader has to work it out.

2. "When are you open on Sunday?" It gives the Saturday hours, because "open" matches. The
handbook says nothing about Sunday, so the right answer is "the handbook does not say". Counting
shared words cannot separate a near match from a right one.

Next I plan to add a minimum overlap so that weak matches say "I don't know".
