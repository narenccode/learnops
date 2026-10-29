This week I made my assistant answer questions from a document, the Zephyr Lane Tool Library
handbook. It splits the handbook into paragraphs and returns the paragraph that shares the most
words with the question. I tested it with ten questions that I wrote before looking at the output.

Two questions it answers badly:

1. "Can I take a sander home for two weeks?" It returns the paragraph about borrowing, which says
seven days, but it never says "no". The assistant only returns text; it cannot compare two weeks
with seven days, so the learner has to work out the answer.

2. "When are you open on Sunday?" It returns the Saturday opening hours, because "open" matches.
The handbook says nothing about Sunday, so the honest answer is "the handbook does not say". Word
overlap cannot tell a near match from a correct one.

Next week I want to add a minimum overlap score so that weak matches return "I don't know".
