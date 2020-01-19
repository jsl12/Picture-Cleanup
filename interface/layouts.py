from ipywidgets import Layout as ly

top_level = ly(
    display='flex',
    flex_flow='column nowrap',
    # border='solid 1px blue'
)
flex_col = ly(
    display='flex',
    flex_flow='column nowrap',
    flex='1 1 40%',
    padding='5px',
    # border='solid 1px red',
)
opts_col = ly(
    display='flex',
    flex_flow='column nowrap',
    flex='1 1 auto',
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