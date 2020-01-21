from ipywidgets import Layout as ly

top_level = ly(
    display='flex',
    flex_flow='column nowrap',
    # border='solid 1px blue'
)

options_section = ly(
    display='flex',
    flex='1 1 auto',
    # width='100%',
    # border='solid 1px red'
    overflow='hidden'
)

options_container = ly(
    display='flex',
    flex='9 1 0%',
    flex_flow='column nowrap',
    # border='solid 1px green'
)

opts_bar = ly(
    display='flex',
    flex='1 1 auto',
    width='100%'
)

output = ly(
    display='flex',
    width='250px',
    # border='solid 1px green'
)

exclude_col = ly(
    display='flex',
    flex='1 1 0%',
    flex_flow='column nowrap',
    # padding='15px',
    # border='solid 1px green'
)

exclude_section = ly(
    display='flex',
    flex='1 1 auto',
    flex_flow='row nowrap',
    width='100%',
    padding='15px',
    # border='solid 1px red'
)