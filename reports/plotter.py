import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objects import Figure
import pandas as pd


class Plotter:
    def __init__(self) -> None:
        self.width = 600
        self.height = 350
        self.margin = dict(t=40, b=60, l=0, r=0)
        self.paper_bgcolor = "LightSteelBlue"
        self.legend = dict(
            orientation="h",
            xanchor="center",
            x=0.5,
            y=-0.3,  # Drop legend below xaxis label
            bgcolor="LightBlue",
            bordercolor="Black",
            borderwidth=2,
            title_text="",
        )
        self.config = {"modeBarButtons": [["toImage"]], "displaylogo": False}
        # self.config = {"staticPlot": True}
        self.layout = dict(
            margin=self.margin,
            legend=self.legend,
            paper_bgcolor=self.paper_bgcolor,
        )
        self.colors = dict(
            Spent="#882255",
            CO="#ddcc77",
            PC="#afeeee",
            FR="#fa8072",
            MLE="#5500ff",
            LE="lightgreen",
            HE="slategrey",
        )

    def bar_chart(
        self, df: pd.DataFrame, x: str, y: list, fig_title: str, hline=0, hline_annotation=None
    ) -> Figure:
        fig_bar = px.bar(
            df,
            barmode="group",
            x=x,
            y=y,
            color_discrete_map=self.colors,
            title=fig_title,
            height=self.height,
            width=self.width,
        )
        fig_bar.update_layout(self.layout)

        if hline:
            fig_bar.add_hline(y=hline, annotation_text=hline_annotation, line_dash="dash")
        return fig_bar.to_html(config=self.config)  # .to_html(include_plotlyjs=False, full_html=False)

    def bullet_chart(
        self,
        df: pd.DataFrame,
        fig_title,
        x_values: list,
        y: str,
        piston: float,
        piston_name: str,
        diamond: str,
        diamond_name: str,
        v_line: float = None,
        v_line_text: str = None,
    ) -> Figure:
        fig_hbar = px.bar(
            df,
            y=y,
            x=x_values,
            color_discrete_map=self.colors,
            title=fig_title,
            height=self.height,
            width=self.width,
            orientation="h",
        )
        fig_hbar.update_layout(self.layout)

        # Piston
        fig_hbar.add_bar(
            x=df[piston],
            y=df[y],
            name=piston_name,
            base=0,
            width=0.25,
            marker=dict(color="slategray"),
            row=1,
            col=1,
            orientation="h",
        )
        # diamond
        fig_hbar.add_scatter(
            x=df[diamond],
            y=df[y],
            name=diamond_name,
            mode="markers",
            marker_symbol="diamond-tall",
            marker_line_width=2,
            marker_size=15,
            marker_line_color="midnightblue",
            marker_color="yellow",
        )
        if v_line:
            # vertical line marker
            fig_hbar.add_vline(x=v_line, annotation_text=v_line_text, line_dash="dash")

        return fig_hbar.to_html(config=self.config)

    def line_chart(self, df: pd.DataFrame, x: str, y: list) -> Figure:
        fig_line = px.line(
            df,
            x=x,
            y=y,
            color_discrete_map=self.colors,
            height=self.height,
            width=self.width,
        ).update_layout(self.layout)
        fig_line.update_traces(textposition="bottom right")
        return fig_line.to_html(config=self.config)

    def pie_chart(self, labels: list, values: list) -> Figure:
        fig_pie = px.pie(
            data_frame=pd.DataFrame({"names": labels, "values": values}),
            values="values",
            names="names",
            title="Current Quarter Encumbrance ",
            height=self.height,
            width=self.width / 2,
            color_discrete_map=self.colors,
        ).update_layout(self.layout)
        return fig_pie.to_html(config=self.config)
