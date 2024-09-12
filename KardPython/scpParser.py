import os
import struct
import re

class SCPParser:
    

    def extract_info_from_scp(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                file_bytes = file.read()

            # Convert the byte array to a string, ensuring UTF-8 encoding to handle Turkish characters
            content = file_bytes.decode('utf-8', errors='ignore')

            # Find the starting point of the data block after "SCPECG"
            start_index = content.find("SCPECG")
            if start_index == -1:
                return {"error": "SCPECG marker not found."}

            # Skip the "SCPECG" marker and any other initial characters
            content = content[start_index + len("SCPECG"):]

            # Find the position of "1958" or another marker to limit the extraction range
            end_index = content.find("1958")
            if end_index == -1:
                return {"error": "End marker not found."}

            # Extract the substring between the markers
            relevant_content = content[:end_index]

            # Split the content by non-word characters, preserving Turkish characters
            words = re.split(r'\W+', relevant_content)
            name = ''
            id = ''

            # Iterate over the words to find the name and ID
            for word in words:
                if len(word) > 1 and not id:
                    if re.match(r'^\d+$', word):  # Word is numeric, likely the ID
                        id = word
                    else:
                        if name:
                            name += ' '
                        name += word  # Add to the name

            # Split the name into first and last names
            name_parts = name.split()
            if len(name_parts) > 1:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])
            else:
                first_name = name_parts[0] if name_parts else ''
                last_name = ''

            if first_name and id:
                return {
                    "first_name": first_name,
                    "last_name": last_name,
                    "id": id
                }

            return {"error": "Patient information not found."}

        except Exception as ex:
            return {"error": f"Error reading the file: {str(ex)}"}

    def read_scp_file(self, file_path):
        try:
            # Read the SCP-ECG file and extract ECG data
            with open(file_path, 'rb') as file:
                file_bytes = file.read()

            # Extract ECG data from the fileBytes
            ecg_data = self.extract_ecg_data(file_bytes)

            return ecg_data
        except Exception as ex:
            print(f"Error reading the SCP-ECG file: {str(ex)}")
            return None


    def extract_ecg_data(self, file_bytes):
        try:
            print("Starting SCP-ECG data extraction...")

            # Define how many leads are expected
            num_leads = 8  # For example: I, II, V1, V2, V3, V4, V5, V6
            expected_length = 100  # Adjust this to your expected minimum file size

            # Check if the file has sufficient length
            if len(file_bytes) < expected_length:
                raise Exception(f"File is too short to be a valid SCP-ECG file. Expected at least {expected_length} bytes.")

            # Create an array to hold the ECG data for each lead
            ecg_data = [[] for _ in range(num_leads)]

            # Loop through each lead and extract data
            for lead_index in range(num_leads):
                print(f"Parsing lead {lead_index + 1}...")

                # Set the starting index for this lead
                start_index = 1000 + (lead_index * 1000)  # Adjust this to your format

                # Ensure that the start index is within bounds
                if start_index >= len(file_bytes):
                    raise Exception(f"Invalid SCP-ECG file: insufficient data length for lead {lead_index + 1}.")

                # Determine the number of data points to extract for this lead
                num_data_points = 5000  # Adjust based on actual data format

                # Ensure we do not read beyond the file bounds
                if start_index + num_data_points * 2 > len(file_bytes):
                    raise Exception(f"Invalid SCP-ECG file: insufficient data length for lead {lead_index + 1}.")

                # Initialize the array to store data for this lead
                ecg_data[lead_index] = [0] * num_data_points

                # Extract the data points
                for i in range(num_data_points):
                    # Convert two bytes to a 16-bit signed integer (ECG data point)
                    ecg_data[lead_index][i] = -struct.unpack('<h', file_bytes[start_index + i * 2:start_index + i * 2 + 2])[0]

                print(f"Lead {lead_index + 1} parsed successfully.")

            # Now, calculate the additional leads
            lead_I = ecg_data[0]
            lead_II = ecg_data[1]
            num_data_points = len(lead_I)

            # Lead III = Lead II - Lead I
            lead_III = [lead_II[i] - lead_I[i] for i in range(num_data_points)]
            ecg_data.append(lead_III)

            # aVR = -(Lead I + Lead II) / 2
            lead_aVR = [-(lead_I[i] + lead_II[i]) / 2 for i in range(num_data_points)]
            ecg_data.append(lead_aVR)

            # aVL = (Lead I - Lead III) / 2
            lead_aVL = [(lead_I[i] - lead_III[i]) / 2 for i in range(num_data_points)]
            ecg_data.append(lead_aVL)

            # aVF = (Lead II + Lead III) / 2
            lead_aVF = [(lead_II[i] + lead_III[i]) / 2 for i in range(num_data_points)]
            ecg_data.append(lead_aVF)

            print("SCP-ECG data extraction completed successfully.")
            return ecg_data

        except Exception as ex:
            print(f"Error during SCP-ECG data extraction: {str(ex)}\n{ex.__traceback__}")
            raise  # Rethrow the exception so that it can be caught in the calling method
    def get_patient_info(self, file_path):
        return self.extract_info_from_scp(file_path)