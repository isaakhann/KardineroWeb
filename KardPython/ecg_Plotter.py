import plotly.graph_objs as go
from markupsafe import Markup
import numpy as np

class EcgPlotter:
    def __init__(self, ecg_data):
        self.ecg_data = ecg_data
        self.lead_names = [
            "Lead I", "Lead II", "Lead III", "Lead V1", "Lead V2",
            "Lead V3", "Lead V4", "Lead V5", "Lead V6", "Lead aVR", "Lead aVL", "Lead aVF"
        ]

    def generate_plot(self, lead_name):
        lead_index = self.lead_names.index(lead_name)
        lead_data = self.ecg_data[lead_index]

        fig = go.Figure()

        # Create the ECG plot
        fig.add_trace(go.Scatter(x=np.arange(len(lead_data)), y=lead_data, mode='lines', name=lead_name))

        # Customize the layout
        fig.update_layout(
            title=lead_name,
            xaxis_title='Time',
            yaxis_title='Amplitude',
            template='plotly_dark'
        )

        # Render the figure as an HTML div
        plot_html = fig.to_html(full_html=False)

        return Markup(plot_html)
