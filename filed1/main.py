import os
import pandas as pd
import requests
import urllib.parse
import hashlib
import paramiko
from datetime import datetime

# Define the API endpoint and headers for authentication
api_endpoint = "https://isdb.apple.com/ui/api/v1/services/1e7768eb-29fa-4cdc-903f-3747c92c4621/vulnerabilities"
api_key = '8c408e46209a1f568d29b37c552aeda1'  # Replace with your actual API key

# Define the directory where you want to save the CSV file
save_directory = '/Users/e009543/Downloads/'

# Define the path to the IP priorities file
ip_priorities_file_path = '/Users/e009543/Desktop/ip_priorities.csv'  # Provide the path to your IP priorities file

# Function to download the CSV file
def list_vulnerabilities(vulnerability_name, save_directory):
    encoded_string = urllib.parse.quote(vulnerability_name)

    url = f"https://isdb.apple.com/ui/api/v1/services/1e7768eb-29fa-4cdc-903f-3747c92c4621/vulnerabilities/export.csv?q={encoded_string}&sev=none"

    headers = {
        'authority': 'isdb.apple.com',
        'x-api-key': '8c408e46209a1f568d29b37c552aeda1'
    }
    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        # Generate a unique filename based on the vulnerability name
        filename = os.path.join(save_directory, f"{hashlib.md5(vulnerability_name.encode()).hexdigest()}.csv")
        with open(filename, 'wb') as csv_file:
            csv_file.write(response.content)
        print(f"CSV file downloaded and saved at: {filename}")
        return filename
    else:
        print(f"Error downloading CSV from the API. Status Code: {response.status_code}")
        return None

# Process the downloaded CSV file and create a new file with selected columns and update IP priorities
def process_vulnerability_csv(input_file_path, save_directory, vulnerability_name, ip_priorities_file_path, command):
    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(input_file_path)

        # Select the specified columns from the downloded file
        selected_columns = ['title', 'ip', 'hostname']
        selected_data = df[selected_columns]

        # Add new columns without any values
        selected_data['priority'] = ''
        selected_data['Vulnerable Version'] = ''
        selected_data['Patch Version'] = ''
        selected_data['Status'] = ''

        # Generate a unique filename for the processed data
        new_filename = os.path.join(save_directory, f"{hashlib.md5(vulnerability_name.encode()).hexdigest()}_processed.csv")

        # Load the IP priorities CSV file
        ip_priorities_df = pd.read_csv(ip_priorities_file_path)

        # Iterate through the rows and update priorities based on IP priorities
        for index, row in selected_data.iterrows():
            ip = row['ip']
            matching_row = ip_priorities_df[ip_priorities_df['ip'] == ip]
            if not matching_row.empty:
                selected_data.at[index, 'priority'] = matching_row.iloc[0]['priority']

        # Save the updated data to a new CSV file
        selected_data.to_csv(new_filename, index=False)

        print(f"New file created: {new_filename}")

        # Initialize SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Iterate through the rows of the DataFrame
        for index, row in selected_data.iterrows():
            ip = row['ip']
            username = 'devadmin'  # Replace with your SSH username
            password = '1nt3r@ctive$123'  # Replace with your SSH password

            try:
                # Set up SSH connection
                ssh.connect(ip, username=username, password=password)

                stdin, stdout, stderr = ssh.exec_command(command)
                version_output = stdout.read().decode().strip()

                print(f"IP: {ip}, Command: {command}, Vulnerable Version: {version_output}")

                # Close the SSH connection
                ssh.close()

                # Update the corresponding columns in the CSV file
                selected_data.at[index, 'Vulnerable Version'] = version_output

            except Exception as e:
                print(f"Error accessing {ip}: {e}")

        # Save the updated DataFrame to the CSV file
        selected_data.to_csv(new_filename, index=False)

        print("Vulnerable Version information and priority updated.")
    except Exception as e:
        print(f"Error processing CSV: {e}")

# Prompt the user to enter the vulnerability name
vulnerability_name = input("Enter the vulnerability name: ")

try:
    # Prompt the user to enter the command to check the version
    command = input("Enter the command to check the version: ")

    # Call the list_vulnerabilities function to retrieve vulnerability data and save it to the specified directory
    downloaded_file_path = list_vulnerabilities(vulnerability_name, save_directory)

    if downloaded_file_path:
        # Process the downloaded CSV file and create a new file with selected columns and update IP priorities
        process_vulnerability_csv(downloaded_file_path, save_directory, vulnerability_name, ip_priorities_file_path, command)

except Exception as e:
    print(f"Error: {e}")

# Continue with the rest of your code.
