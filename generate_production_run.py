import numpy as np
import pandas as pd


def merging_dfs(materials_df, customer_df):

    # Breaking down a stackup into each individual ply (i.e. A0/A90/A90/A0 --> A0,A90,A90,A0)
    customer_df = customer_df.assign(**{'ply breakdown': customer_df['STACKUP'].str.split('/')}).explode('ply breakdown', ignore_index=True)

    # Cleaning the ply breakdown data
    customer_df['ply breakdown'] = customer_df['ply breakdown'].fillna('').astype(str)

    # Extract material and angle, handle potential conversion issues
    customer_df['material'] = customer_df['ply breakdown'].str[0]
    customer_df['angle'] = customer_df['ply breakdown'].str[1:]

    # Handle empty strings and non-digit values
    customer_df['angle'] = customer_df['angle'].apply(lambda x: int(x) if x.isdigit() else None)

    # Filter out rows with invalid angle values
    customer_df = customer_df.dropna(subset=['angle'])

    # Convert angle column to integer
    customer_df['angle'] = customer_df['angle'].astype(int)

    # Determining the complementary angle (75 deg --> 15 deg)
    customer_df['cutangle'] = customer_df['angle'].apply(lambda angle: 90 - angle if 45 < angle < 90 else angle).apply(abs)

    # Counts repeated plies, where we consider repeats those that share the same panel length/width/material/cut angle
    customer_df['ply counts'] = customer_df.groupby(['material', 'cutangle', 'PANEL LENGTH', 'PANEL WIDTH']).cumcount() + 1

    # Removes duplicates keeping only the most recent count of repeats
    customer_df = customer_df.drop_duplicates(subset=['material', 'cutangle', 'PANEL LENGTH', 'PANEL WIDTH'], keep='last')

    # Assigning the material convention (the respective letters) to an actual product number
    customer_df['product number'] = customer_df.apply(lambda row: next(
        (value.split(':')[1] for value in row['COMPOSITION CODE'].split(',')
         if value.split(':')[0] == row['material']), None), axis=1).astype(str)

    # Crossmatching the order with the materials database using the product number
    merged_dfs = customer_df.merge(materials_df, left_on='product number', right_on='PN Concatenation', how='inner')

    return merged_dfs

    

def initial_cut_length(row):
    cutangle = row['cutangle']
    if cutangle != 90 and cutangle != 0:
        radians = np.radians(cutangle)
        effective_panel_width = row['PANEL WIDTH'] / np.sin(radians)
        first_cut_length = np.ceil((row['PANEL LENGTH'] / np.cos(radians) * 8) / 8)
    elif cutangle == 0:
        first_cut_length = row['PANEL LENGTH']
    else:  # cutangle == 90
        first_cut_length = row['PANEL WIDTH']
    
    return first_cut_length

def initial_number_of_cuts(row):
    cutangle = row['cutangle']
    effective_panel_width = 0
    if cutangle != 0 and cutangle != 90:
        radians = np.radians(cutangle)
        effective_panel_width = row['PANEL WIDTH'] / np.sin(radians)
    elif cutangle == 0:
        effective_panel_width = row['PANEL WIDTH']
    elif cutangle == 90:
        effective_panel_width = row['PANEL LENGTH']
    
    number_of_panels = row['TARGET PARTS'] / (row['PARTS/LENGTH'] * row['PARTS/WIDTH'])
    cutValue = np.ceil((number_of_panels * row['ply counts'] * effective_panel_width) / row['Width (in)'])
    return cutValue


def secondary_number_of_cuts(row):
    number_of_panels = row['TARGET PARTS'] / (row['PARTS/LENGTH'] * row['PARTS/WIDTH'])
    cutValue = np.ceil(number_of_panels * row['ply counts'])
    return cutValue

def secondary_cut_length(row):
    cutangle = row['cutangle']
    if cutangle != 90 and cutangle != 0:
        radians = np.radians(cutangle)
        effective_panel_width = row['PANEL WIDTH'] / np.sin(radians)
        second_cut_length = np.ceil((effective_panel_width / np.cos(radians) * 8) / 8)
    elif cutangle == 0:
        second_cut_length = row['PANEL WIDTH']
    else:  # cutangle == 90
        second_cut_length = row['PANEL LENGTH']
    
    return second_cut_length


def calculations(materials_df, customer_df):
    ### length of first set of cuts
    df = merging_dfs(materials_df, customer_df)

    # List of columns to exclude from conversion
    columns_to_exclude = [
        'CLIENT', 'PART', 'STACKUP', 'COMPOSITION CODE', 'ply breakdown', 'material', 'product number',
        'Description', 'Previously Called', 'TYPE', 'Fiber Category', 'Resin Category',
        'Sequence Assist', 'Auto-Sequence', 'PN Concatenation', 'PN+Description Concatenation',
        'UOM', 'Manufacturer', 'Manufacturer PN (link to datasheet)',
        'Misc. Notes', 'Weld Notes:', 'Cut Notes:', 'Inventory Locations:'
    ]
    
    # Get the list of columns to convert to numeric
    columns_to_convert = [col for col in df.columns if col not in columns_to_exclude]
    
    # Convert the selected columns to numeric
    df[columns_to_convert] = df[columns_to_convert].apply(pd.to_numeric, errors='coerce')
    
    ### creating a column for the length of the first cuts
    df['initial_cut_length'] = df.apply(initial_cut_length,axis=1)
    
    ### creating a column for the length of the first cuts
    df['initial_number_of_cuts'] = df.apply(initial_number_of_cuts,axis=1)
    
    ### number of welds
    df['number_of_welds'] = df.apply(initial_number_of_cuts,axis=1)-1
    
    ### length of second set of cuts
    df['secondary_cut_length'] = df.apply(secondary_cut_length,axis=1)
    
    ### creating a column for the length of the first cuts
    df['secondary_number_of_cuts'] = df.apply(secondary_number_of_cuts,axis=1)
    
    return df

