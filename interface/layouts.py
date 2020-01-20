from ipywidgets import Layout as ly

top_level = ly(
    display='flex',
    flex_flow='column nowrap',
    # border='solid 1px blue'
)

flex_col = ly(
    display='flex',
    flex_flow='column nowrap',
    flex='0 1 40%',
    padding='10px',
    # border='solid 1px red',
)

select_label = ly(
    display='flex',
    flex='0 1 auto',
    # border='solid 1px green'
)

col_select = ly(
    display='flex',
    flex='1 1',
    height='100%',
    width='100%'
)

o = 'hidden'
opts_col = ly(
    display='flex',
    flex='1 1 0%',
    flex_flow='column nowrap',
    align_items='stretch',
    padding='10px',
    # border='solid 1px red',
)

dup_type = ly(
    display='flex',
    flex='0 1 auto',
    width='100%',
    # padding='10px',
    # border='solid 1px blue'
)

dup_button = ly(
    display='flex',
    flex='0 1 auto',
    # height='25%',
    width='100%',
    align_self='center',
)
