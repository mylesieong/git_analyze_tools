import subprocess
import pandas as pd
import sys

import re

def get_insertions_number(commit_stats):
    # Define a regular expression pattern to match insertions and deletions information
    pattern = r"\d+ insertions\(\+\)"

    # Find all matches using the regular expression pattern
    matches = re.findall(pattern, commit_stats)

    if matches:
        # Extract the numeric value from the first match
        insertions = int(re.search(r"\d+", matches[0]).group())
        return insertions
    else:
        return 0

def get_deletions_number(commit_stats):
    # Define a regular expression pattern to match insertions and deletions information
    pattern = r"\d+ deletions\(\-\)"

    # Find all matches using the regular expression pattern
    matches = re.findall(pattern, commit_stats)

    if matches:
        # Extract the numeric value from the first match
        insertions = int(re.search(r"\d+", matches[0]).group())
        return insertions
    else:
        return 0

def git_log():
    # Run 'git log --stat' command and capture the output
    git_log_output = subprocess.check_output(['git', 'log', '-100', '--date=short', '--pretty=format:%h|%an|%ad|%s'])
    git_log_output = git_log_output.decode('utf-8').strip()

    # Split each line of git log output
    log_lines = git_log_output.split('\n')

    # Create a list to store log details
    log_data = []

    for line in log_lines:
        # Split each line into commit hash, author name, date, and commit message
        commit_hash, author_name, date, commit_msg = line.split('|')

        # Get the diffstat for the commit
        diffstat = subprocess.check_output(['git', 'diff', '-w', commit_hash, commit_hash + '^', '--stat'])
        diffstat = diffstat.decode('utf-8').strip()

        # Extract the number of insertions and deletions from the diffstat
        insertions, deletions = 0, 0
        for stat_line in diffstat.split('\n'):
            if 'insertions' in stat_line:
                insertions += get_insertions_number(stat_line)
            if 'deletions' in stat_line:
                deletions += get_deletions_number(stat_line)

        data = {
            'Commit Hash': commit_hash,
            'Author': author_name.lower(),
            'Date': date,
            'Commit Message': commit_msg,
            'Additions': insertions,
            'Deletions': deletions,
            'Differences': insertions + deletions 
        }

        log_data.append(data)

    return log_data

def generate_contribution_table(log_data, type_data):
    # Convert the log data to a DataFrame
    df = pd.DataFrame(log_data)

    # Convert the 'Date' column to datetime type
    df['Date'] = pd.to_datetime(df['Date'])

    # Group by 'Author' and 'Date' to get the number of commits, additions, and deletions per day for each team member
    if type_data == "c":
        contributions = df.groupby(['Author', 'Date']).agg({
            'Commit Hash': 'count'
        }).reset_index()
    elif type_data == "a":
        contributions = df.groupby(['Author', 'Date']).agg({
            'Additions': 'sum'
        }).reset_index()
    elif type_data == "d":
        contributions = df.groupby(['Author', 'Date']).agg({
            'Deletions': 'sum'
        }).reset_index()
    elif type_data == "t":
        contributions = df.groupby(['Author', 'Date']).agg({
            'Differences': 'sum'
        }).reset_index()

    # Pivot the data to transform authors into columns and dates into rows
    contribution_table = contributions.pivot(index='Date', columns='Author')

    contribution_table.fillna('-', inplace=True)

    return contribution_table

def main():
    if len(sys.argv) < 2:
        print("Usage: python script_name.py [c|a|d|t]")
        return

    type_data = sys.argv[1]
    try:
        log_data = git_log()
        contribution_table = generate_contribution_table(log_data, type_data)
        print(contribution_table)
    except subprocess.CalledProcessError as e:
        print("Error running 'git log' command:", e)
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
