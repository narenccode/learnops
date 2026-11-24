import sys
sys.path.insert(0, '.')
from docx import Document
from docx.shared import Pt
from notes_data import NOTES, TITLES

d = Document()
st = d.styles['Normal']
st.font.name = 'Arial'
st.font.size = Pt(10.5)
d.add_heading('LearnOps Interim Presentation: Speaker Notes', 0)
d.add_paragraph('Source: GitHub audit of narenccode/learnops, main at ecb4389, fetched 2026-11-16. '
                'Status claims follow that audit. Registration numbers, batch number, mentor details and the '
                'approved proposal were not supplied and appear as placeholders.')
for n in range(1, 16):
    x = NOTES[n]
    d.add_heading(f'Slide {n}: {TITLES[n-1]}', 1)
    d.add_heading('What to explain', 2)
    for t in x['explain']:
        d.add_paragraph(t, style='List Bullet')
    d.add_heading('Technical detail', 2)
    for t in x['details']:
        d.add_paragraph(t, style='List Bullet')
    d.add_heading('Likely evaluator questions', 2)
    for q, a in x['qa']:
        p = d.add_paragraph()
        r = p.add_run('Q: ' + q)
        r.bold = True
        d.add_paragraph('A: ' + a)
d.save('LearnOps_Presentation_Speaker_Notes.docx')
