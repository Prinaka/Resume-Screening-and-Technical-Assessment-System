import altair as alt
import pandas as pd


def arc(data, label, colours):
    return alt.Chart(data).mark_arc(innerRadius=80).encode(
        theta="%", color=alt.Color("Topic:N", scale=alt.Scale(domain=[label, ''], range=colours), legend=None)
        ).properties(width=250, height=250)


def make_donut(value, label):
    colours = (
            ['#12783D', '#27AE60',] if value >= 70 else
            ['#875A12', '#F39C12', ] if value >= 50 else
            ['#781F16', '#E74C3C',]
            )
    base = pd.DataFrame({"Topic": ['', label], "%": [value, 100 - value, ]})
    bg = pd.DataFrame({"Topic": ['', label], "%": [100, 0]})
        
    text = alt.Chart(base).mark_text(
        align='center', color="white", font="Calibri",
        fontSize=30, fontWeight=700, fontStyle="Bold"
        ).encode(text=alt.value(f"{value} %"))
        
    return arc(bg, label, colours) + arc(base, label, colours) + text


def bar_chart(scores_df, x, y):
    chart = alt.Chart(scores_df).mark_bar(cornerRadius=8).encode(
            x=alt.X(x, scale=alt.Scale(domain=[0, 100])),
            y=alt.Y(y, sort="-x"),
            color=alt.Color(y, legend=None)
            )
    return chart

def comparison_chart(skill_data):

    chart = alt.Chart(skill_data).mark_arc(innerRadius=60).encode(
        theta="Count",
        color="Category",
        tooltip=["Category", "Count"]
        ).properties(width=300, height=300)
    return chart
