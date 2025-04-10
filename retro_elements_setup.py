import streamlit as st
from streamlit_elements import elements, mui
import random

st.set_page_config(layout="wide")

# Retro CRT styling
crt_style = """
<style>
body {
    background: #000 !important;
    font-family: 'Courier New', monospace !important;
}

#outer-frame {
    border: 8px double #00ffff;
    padding: 20px;
    margin: 10px;
    box-shadow: 0 0 30px #00ffff, inset 0 0 10px #00ffff;
    background: #000;
    position: relative;
}

.terminal {
    background: radial-gradient(circle, #001122 0%, #000000 100%) !important;
    border: 4px solid #00ffff !important;
    border-radius: 10px !important;
    box-shadow: inset 0 0 15px #00ffff !important;
    color: #0f0 !important;
}

.scanline {
    position: absolute;
    width: 100%;
    height: 2px;
    background: rgba(0, 255, 255, 0.1);
    animation: scan 4s linear infinite;
}

@keyframes scan {
    0% { top: 0; }
    100% { top: 100%; }
}
</style>
"""
st.markdown(crt_style, unsafe_allow_html=True)

# Layout structure
with st.container():
    st.markdown('<div id="outer-frame"><div class="scanline"></div>', unsafe_allow_html=True)
    with elements("crt_dashboard"):
        # Main flex container
        with mui.Box(display="flex", height="90vh", gap=4):
            
            # Left Clipboard (Vertical)
            with mui.Box(
                width="30%",
                className="terminal",
                sx={
                    "p": 2,
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": 2
                }
            ):
                mui.Typography("CODE CLIPBOARD", variant="h5", color="#00ffff", textAlign="center")
                mui.TextField(
                    multiline=True,
                    fullWidth=True,
                    rows=25,
                    variant="outlined",
                    placeholder="PASTE CODE HERE...",
                    sx={
                        "textarea": {"color": "#0f0"},
                        "fieldset": {"borderColor": "#00ffff !important"},
                        "flexGrow": 1
                    }
                )
            
            # Right Side Screens
            with mui.Box(
                width="70%",
                display="flex",
                flexDirection="column",
                gap=4
            ):
                # TV Screen 1
                mui.Paper(
                    className="terminal",
                    sx={
                        "height": "48%",
                        "p": 2,
                        "position": "relative",
                        "overflow": "hidden"
                    },
                    children=[
                        mui.Typography("SYSTEM MONITOR 1", color="#00ffff"),
                        html.div(className="scanline")
                    ]
                )
                
                # TV Screen 2
                mui.Paper(
                    className="terminal",
                    sx={
                        "height": "48%",
                        "p": 2,
                        "position": "relative",
                        "overflow": "hidden"
                    },
                    children=[
                        mui.Typography("SYSTEM MONITOR 2", color="#00ffff"),
                        html.div(className="scanline")
                    ]
                )

    st.markdown('</div>', unsafe_allow_html=True)