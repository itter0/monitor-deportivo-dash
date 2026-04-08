import dash
from dash import dcc, html, Input, Output, State, callback_context, ALL
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import json
import pandas as pd
import numpy as np
from urllib.parse import urlparse, parse_qs, urlencode
import os
import re 
import subprocess
import signal
import threading
import csv  
import time 
import base64

from tactical_system import (
    OpponentProfile,
    TacticalPlan,
    OpponentStyle,
    CampPhase,
    generate_initial_tactical_plan,
    validate_plan_advanced,
    generate_training_calendar,
    generate_calendar_pdf,
)

