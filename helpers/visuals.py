import altair as alt
import pandas as pd


def arc(data, label, colours, radius=85, corner=20):
    return alt.Chart(data).mark_arc(innerRadius=radius, cornerRadius=corner).encode(
        theta="%", color=alt.Color("Topic:N", scale=alt.Scale(domain=[label, ''], range=colours), legend=None)
        ).properties(width=250, height=250)


def make_donut(value, label):
    colours = (
            ['#27AE60', '#12783D'] if value >= 80 else
            ['#F39C12', '#875A12'] if value >= 50 else
            ['#E74C3C', '#781F16']
            )
    base = pd.DataFrame({"Topic": ['', label], "%": [100 - value, value]})
    bg = pd.DataFrame({"Topic": ['', label], "%": [100, 0]})
        
    text = alt.Chart(base).mark_text(
        align='center', color="white", font="Calibri",
        fontSize=25, fontWeight=700, fontStyle="Bold"
        ).encode(text=alt.value(f"{value} %"))
        
    return arc(bg, label, colours) + arc(base, label, colours) + text
