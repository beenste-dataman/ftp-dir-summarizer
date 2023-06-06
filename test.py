#ccd

import os
import time
import base64
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import webbrowser
import urllib.parse
from jinja2 import Template

# Ask the user for the FTP directory path
dir_path = input('Enter the path to the FTP directory: ')

# Initialize counters for total file and directory counts
file_count = 0
dir_count = 0

# Initialize lists to store file and directory data
file_data = {
    'name': [],
    'path': [],
    'size': [],
    'modification_time': [],
    'owner': [],
}
dir_data = {
    'name': [],
    'path': [],
    'owner': [],
}

# Walk the directory tree
for dirpath, dirnames, filenames in os.walk(dir_path):
    dir_count += len(dirnames)
    for dirname in dirnames:
        dirpath_full = os.path.join(dirpath, dirname)
        stat = os.stat(dirpath_full)
        dir_data['name'].append(dirname)
        dir_data['path'].append(dirpath_full)
        dir_data['owner'].append(stat.st_uid)
    for filename in filenames:
        filepath = os.path.join(dirpath, filename)
        try:
            stat = os.stat(filepath)
            file_data['name'].append(filename)
            file_data['path'].append(filepath)
            file_data['size'].append(stat.st_size)
            file_data['modification_time'].append(stat.st_mtime)
            file_data['owner'].append(stat.st_uid)
            file_count += 1
        except FileNotFoundError:
            print(f"File not found: {filepath}")

# Create a DataFrame from the file data
df = pd.DataFrame(file_data)
df['filetype'] = df['name'].apply(lambda x: os.path.splitext(x)[1])

# Create a DataFrame from the directory data
df_dirs = pd.DataFrame(dir_data)

# Filter out files with blank extensions
df = df[df['filetype'] != '']

# Generate summary statistics
summary = pd.DataFrame({
    'Total file count': [len(df)],
    'Total directory count': [len(df_dirs)],
})

# Generate the owner-to-filetype count table
owner_filetype_count = df.groupby(['owner', 'filetype']).size().unstack().fillna(0).astype(int)

# Create graphs
if not df.empty:
    fig, ax = plt.subplots(figsize=(10,6))
    df['modification_time'].apply(lambda x: time.strftime('%Y-%m', time.gmtime(x))).value_counts().sort_index().plot(ax=ax)
    plt.title('Time series graph of file modification')
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    modification_times_uri = 'data:image/png;base64,' + urllib.parse.quote(string)

    fig, ax = plt.subplots(figsize=(10,6))
    df['owner'].value_counts().plot(kind='bar', ax=ax)
    plt.title('Bar graph showing the number of files owned by each user')
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    file_owners_uri = 'data:image/png;base64,' + urllib.parse.quote(string)

    fig, ax = plt.subplots(figsize=(10,6))
    df['filetype'].value_counts().plot(kind='bar', ax=ax)
    plt.title('Bar graph showing the count of all files by file type')
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    file_counts_by_type_uri = 'data:image/png;base64,' + urllib.parse.quote(string)
else:
    modification_times_uri = ""
    file_owners_uri = ""
    print("DF is empty, something went wrong!")   
    

# Define a Jinja2 template as a multiline string
template = Template("""
<html>
<head>
    <title>FTP Server Summary</title>
    <style>
        body {
            background-color: #333;
            color: #fff;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 0 20px; /* Add padding to the left and right */
        }
        h1, h2 {
            text-align: center;
        }
        .card {
            width: 200px;
            padding: 20px;
            border-radius: 5px;
            background-color: #444;
            color: #fff;
            margin: 10px;
            text-align: center;
        }
        .cards {
            display: flex;
        }
        img {
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 70%;
        }
        .stats {
            font-family: 'Courier New', monospace;
            margin: 20px;
            text-align: center;
        }
        .container {
            overflow-x: auto;
            padding: 0 20px; /* Add padding to the left and right */
        }
    </style>
</head>
<body>
    <h1>FTP Server Summary</h1>
    <div class="cards">
        <div class="card">
            <h2>Total Files</h2>
            <p>{{ total_files }}</p>
        </div>
        <div class="card">
            <h2>Total Directories</h2>
            <p>{{ total_dirs }}</p>
        </div>
    </div>
    <h2>Summary Statistics</h2>
    <div class="stats">{{ summary }}</div>
    <h2>Owner to Filetype Count</h2>
    <div class="stats">
        <div class="container">
            {{ owner_filetype_count }}
        </div>
    </div>
    <h2>Graphs</h2>
    <img src="{{ modification_times_uri }}" alt="Time series graph of file modification">
    <img src="{{ file_owners_uri }}" alt="Bar graph showing the number of files owned by each user">
    <img src="{{ file_counts_by_type_uri }}" alt="Bar graph showing the count of all files by file type">
</body>
</html>
""")

# Render the template with the summary statistics and graphs
output = template.render(total_files=len(df),
                         total_dirs=len(df_dirs),
                         summary=summary.to_html(),
                         owner_filetype_count=owner_filetype_count.to_html(),
                         modification_times_uri=modification_times_uri,
                         file_owners_uri=file_owners_uri,
                         file_counts_by_type_uri=file_counts_by_type_uri)

# Ask the user for the output file name and path
output_file = input('Enter the name and path of the HTML output file: ')

# Save the output to the HTML file
with open(output_file, 'w') as f:
    f.write(output)

# Open the HTML file in the default web browser
webbrowser.open('file://' + os.path.realpath(output_file))
