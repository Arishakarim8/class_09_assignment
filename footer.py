import streamlit as st
def footer():
    st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f8f9fa;
        color: #6c757d;
        text-align: center;
        padding: 10px;
        font-size: 0.8em;
        border-top: 1px solid #dee2e6;
    }
    </style>
    <div class="footer">
        © 2023 NeoBank | <a href="#privacy" style="color: #6c757d;">Privacy Policy</a> | 
        <a href="#terms" style="color: #6c757d;">Terms of Service</a>
        <a href="#contact" style="color: #6c757d;">Visit www.neobank.com</a>
    </div>
    """,
        unsafe_allow_html=True
    )

    